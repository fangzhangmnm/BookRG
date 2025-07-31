import batchfactory as bf
from batchfactory.op import *
import batchfactory.op.functional as F
import re
from functools import partial
import click
import os

file_dir = os.path.dirname(os.path.abspath(__file__))

pattern = re.compile(r'^[\(（]?注[：:]?.*[\)）]?$',re.M)
def remove_comment(text):
    return pattern.sub('', text)

def merge_small_text(texts, threshold=256):
    new_texts = [""]
    for text in texts:
        if len(new_texts[-1])< threshold:
            new_texts[-1] += text
        else:
            new_texts.append(text)
    return new_texts

def generate_html(data):
    def generate_level(level,pos):
        text = data[f"texts_{level}_rg"][pos]
        children = []
        if level>0:
            parent_map = data[f"parent_map_{level-1}"]
            for k,v in parent_map.items():
                k = int(k)
                if v-1 == pos:
                    children.append(k-1)
        result = "<div>\n"
        for line in text.split("\n"):
            if line.strip():
                result += "<p>"+line+"</p>\n"
        if len(children)>0:
            result += "<ul>\n"
            for child in children:
                result += "<li><details>\n"
                result += generate_level(level-1,child)
                result += "</details></li>\n"
            result += "</ul>\n"
        if level == 0:
            text_detail = data[f"texts_{level}"][pos]
            result += "<details><div>\n"
            for line in text_detail.split("\n"):
                if line.strip():
                    result += "<p>"+line+"</p>\n"
            result += "</div></details>\n"
        result += "</div>\n"
        return result
    filename = data["filename"]
    max_level = max([int(k.split('_')[1]) for k in data.keys() if k.startswith("texts_")])
    result = "<html>\n<body>\n"
    result += f"<h1>{filename}</h1>\n"
    for child in range(len(data[f"texts_{max_level}"])):
        result += generate_level(max_level, child)
    result += "</body>\n</html>"
    return result

def show(x,title=""):
    print(title,x)

def replace_failed_with_empty(text):
    total_chars = len(text)
    total_different_chars = len(set(text))
    repetition = total_chars / total_different_chars if total_different_chars > 0 else 0
    if repetition<10:
        return text
    else:
        return ""

@click.command()
@click.argument('txt_path', type=click.Path(exists=True, dir_okay=False))
@click.option('--overwrite', is_flag=True, default=False, help='Overwrite existing project data')
@click.option('--n_iter', default=3, help='Number of RG iterations')
@click.option('--base_url', default='https://api.lambdalabs.com/v1', help='Provider for the model')
@click.option('--api_key_environ', default='LAMBDA_API_KEY', help='Provider for the model')
@click.option('--model_1', default='deepseek-v3-0324', help='Model to use for RG')
@click.option('--model_2', default='deepseek-r1-671b', help='Model to use for Segmentation')
def book_rg(txt_path,overwrite,n_iter,base_url,api_key_environ,model_1,model_2):
    filename = os.path.splitext(os.path.basename(txt_path))[0]
    txt_path = os.path.abspath(txt_path)
    data_dir = os.path.join(os.path.dirname(txt_path),f"{filename}_data")
    output_json_path = os.path.join(os.path.dirname(txt_path), f"{filename}.json")
    output_html_path = os.path.join(os.path.dirname(txt_path), f"{filename}.html")

    prompt_init_seg = bf.read_txt(os.path.join(file_dir, 'prompts/init_seg.txt'))
    prompt_rg = bf.read_txt(os.path.join(file_dir, 'prompts/rg_v6.txt'))
    prompt_seg = bf.read_txt(os.path.join(file_dir, 'prompts/seg_v5.txt'))
    
    # monkey patch provider and API Key
    print(f"[INFO] 使用模型: {model_1}, {model_2}，请确保这些是你的 provider {base_url} 支持的模型 ID。")
    if not os.getenv(api_key_environ):
        raise RuntimeError(f"请先设置环境变量 {api_key_environ}，否则无法访问模型服务。")
    model_1 += '@custom'
    model_2 += '@custom'
    dummy_desc = {'price_per_input_token_M':0,'price_per_output_token_M':0,'batch_price_discount': 0.5,'chat_completions':True,}
    bf.lib.model_list.model_desc[model_1] = dummy_desc
    bf.lib.model_list.model_desc[model_2] = dummy_desc
    bf.lib.model_list.client_desc['custom']={
        'api_key_environ': api_key_environ,
        'base_url': base_url,
    }

    project = bf.ProjectFolder("book_rg", 0,0,0, data_dir = data_dir)

    if overwrite:
        project.delete_all(warning=False)
    with project:
        # Initial Segmentation

        g = ReadTxtFolder(txt_path)
        g |= MapField(F.remove_markup_header, "text", "text")
        g |= MapField(F.lines, "text", "texts")
        g |= MapField(partial(F.label_and_chunk_texts,chunk_length=15000),"texts","chunks")
        sub = AskLLM(prompt_init_seg,model=model_1,output_key="labels",failure_behavior='retry')
        sub |= MapField(F.text_to_integer_list, "labels")
        g |= ListParallel(sub, "chunks", "text", "labels", "labels")
        g |= MapField(F.postprocess_labels, ["labels", "texts"], ["texts", "parent_map"])
        g |= MapField(partial(show,title=f"labels"),"labels",[])
        g |= RemoveField("labels","parent_map","chunks","text","spawn_idx_list")
        g |= MapField(merge_small_text, "texts", "texts")

        # Start RG Iteration
        g |= RenameField("texts", "texts_0")

        for i in range(n_iter+1):
            # Coarse Graining Text
            g |= MapField(lambda texts:["(N\A)"]+texts[:-1], f"texts_{i}", "prevs")
            sub = AskLLM(prompt_rg, model=model_1, output_key="text_rg",failure_behavior='retry')
            sub |= MapField(replace_failed_with_empty, "text_rg")
            sub |= MapField(remove_comment, "text_rg")
            g |= ListParallel(sub, [f"texts_{i}","prevs"], ["text","prev"], "text_rg", f"texts_{i}_rg")
            g |= RemoveField("spawn_idx_list", "prevs")

            if i == n_iter:
                break

            # Regroup Coarse Grained Texts
            g |= MapField(partial(F.label_and_chunk_texts,chunk_length=15000,multiline=True),f"texts_{i}_rg","chunks")
            sub = AskLLM(prompt_seg,model=model_2,output_key="labels",max_completion_tokens=15000,failure_behavior='retry')
            sub |= MapField(F.text_to_integer_list, "labels")
            g |= ListParallel(sub, "chunks", "text", "labels", "labels")
            g |= MapField(F.postprocess_labels, ["labels", f"texts_{i}_rg"], [f"texts_{i+1}", f"parent_map_{i}"])
            g |= MapField(partial(show,title=f"labels_{i}"),"labels",[])
            g |= RemoveField("labels","chunks","spawn_idx_list")

        g |= OutputEntries()
        g |= WriteJsonl(output_json_path)

    results = g.execute(dispatch_brokers=True)
    data = results[0].data
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(generate_html(data))

    print(f"[INFO] 小说大纲整理完毕. 网页版大纲保存在 {output_html_path}, 原始json文件保存在 {output_json_path}.")

if __name__ == "__main__":
    book_rg()