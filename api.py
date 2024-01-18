import base64
import json
import os
import time

import click
import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

open_url = 'https://open.maze.guru/api/v1'
private_key_path = './private_key.txt'
public_key_path = './public_key.txt'
appid_path = 'appid.txt'
common_headers = {
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.16 Chrome/91.0.4472.164 Electron/13.4.0 Safari/537.36",
}


@click.group()
def cli():
    pass


def get_private_key():
    global s
    if not os.path.exists(private_key_path):
        click.echo(f'{private_key_path} not exist')
        exit(1)
    with open(private_key_path, 'r') as f:
        s = f.read()
    return base64.b64decode(s)


def generate_new_key():
    key = RSA.generate(1024)
    private_key = key.export_key("DER", pkcs=8)
    public_key = key.publickey().export_key("DER")
    return base64.b64encode(private_key).decode('utf-8'), base64.b64encode(public_key).decode('utf-8')


def get_appid():
    global s
    if not os.path.exists(appid_path):
        click.echo(f'{appid_path} not exist, please use command set-appid first')
        exit(1)
    with open(appid_path, 'r') as f:
        s = f.read()
    if s == '':
        click.echo('empty appid, please use command set-appid first')
        exit(1)
    return s


def get_headers():
    appid = get_appid()
    signed = rsa_sign(appid)
    headers = common_headers.copy()
    headers['Authorization'] = signed
    return headers


def response_data(resp):
    if resp.status_code != 200:
        click.echo(f"status code: {resp.status_code}, error: {resp.text}")
        exit(1)

    respData = resp.json()
    if respData['code'] != 200:
        click.echo(f"resp code: {respData['code']}, error: {respData['msg']}")
        exit(1)
    return respData['data']


def post_requests(url, headers, data=None):
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    return response_data(resp)


def get_requests(url, headers):
    resp = requests.get(url, headers=headers)
    return response_data(resp)


# RSA签名
def rsa_sign(appid):
    now = int(time.time())
    plain_text = {
        "appId": appid,
        "timestamp": now
    }
    original = json.dumps(plain_text, separators=(',', ':'))
    pri = get_private_key()
    h = SHA256.new(original.encode('utf-8'))
    signature = pkcs1_15.new(RSA.importKey(pri)).sign(h)
    auth = {
        "appId": appid,
        "secretKeyVersion": "1",
        "sign": str(base64.b64encode(signature), encoding="utf-8"),
        "original": original
    }
    return json.dumps(auth, separators=(',', ':'))


# 生成公私钥
@click.command()
def generate_key():
    pri, pub = generate_new_key()
    with open(private_key_path, 'w') as f:
        f.write(pri)
    with open(public_key_path, 'w') as f:
        f.write(pub)
    click.echo(f'generate keys in {private_key_path}, {public_key_path}')


# 设置appid
@click.command()
@click.option('--appid', required=True, type=str, help='application id')
def set_appid(appid):
    if appid == "":
        click.echo('empty appid')
        return
    with open(appid_path, 'w') as f:
        f.write(appid)
    click.echo(f'success set appid in {appid_path}')


# RSA签名
@click.command()
def sign():
    appid = get_appid()
    signed = rsa_sign(appid)
    click.echo(f'{signed}')


# 获取模型列表
@click.command()
def style_base_infos():
    resp = get_requests(open_url + '/style-base-infos', get_headers())
    click.echo(json.dumps(resp))


# 获取指定的模型资源
@click.command()
@click.option('--style_id', required=True, type=int, help='style id')
def style_resource(style_id):
    params = f'?style_id={style_id}'
    resp = get_requests(open_url + '/style-resource' + params, get_headers())
    click.echo(json.dumps(resp))


# txt2img
@click.command()
@click.option('--style_id', required=True, type=int, help='style id')
@click.option('--prompt', required=True, type=str, help='prompt')
@click.option('--uc_prompt', type=str, help='uc prompt')
@click.option('--width', required=True, type=int, help='width')
@click.option('--height', required=True, type=int, help='height')
@click.option('--num', type=int, default=1, help='number')
@click.option('--art_genre', type=str, help='art genre')
@click.option('--seed', type=str, help='seed')
def txt2img(style_id, prompt, uc_prompt, width, height, num, art_genre, seed):
    req = {
        "style_id": style_id,
        "prompt": prompt,
        "uc_prompt": uc_prompt,
        "width": width,
        "height": height,
        "num": num,
        "art_genre": art_genre,
        "seed": seed
    }
    resp = post_requests(open_url + '/txt2img', get_headers(), req)
    click.echo(json.dumps(resp))


# img2img
@click.command()
@click.option('--style_id', required=True, type=int, help='style id')
@click.option('--prompt', required=True, type=str, help='prompt')
@click.option('--uc_prompt', type=str, help='uc prompt')
@click.option('--width', required=True, type=int, help='width')
@click.option('--height', required=True, type=int, help='height')
@click.option('--init_image_url', required=True, type=str, help='init image url')
@click.option('--init_image_similarity', type=int, default=50, help='init image similarity')
@click.option('--num', type=int, default=1, help='number')
@click.option('--art_genre', type=str, help='art genre')
@click.option('--seed', type=str, help='seed')
def img2img(style_id, prompt, uc_prompt, width, height, init_image_url, init_image_similarity, num, art_genre, seed):
    req = {
        "style_id": style_id,
        "prompt": prompt,
        "uc_prompt": uc_prompt,
        "width": width,
        "height": height,
        "init_image_url": init_image_url,
        "init_image_similarity": init_image_similarity,
        "num": num,
        "art_genre": art_genre,
        "seed": seed
    }
    resp = post_requests(open_url + '/img2img', get_headers(), req)
    click.echo(json.dumps(resp))


# 获取模型列表
@click.command()
@click.option('--jobs', required=True, type=str, help='jobs')
def generate_result(jobs):
    req = {
        "jobs": jobs.split(',')
    }
    resp = post_requests(open_url + '/generate-result', get_headers(), req)
    click.echo(json.dumps(resp))


# 取消作画
@click.command()
@click.option('--job', required=True, type=str, help='job')
def cancel(job):
    req = {
        "job": job
    }
    resp = post_requests(open_url + '/cancel', get_headers(), req)
    click.echo(json.dumps(resp))


# 计算作画成本
@click.command()
@click.option('--style_id', required=True, type=int, help='style id')
@click.option('--prompt', required=True, type=str, help='prompt')
@click.option('--uc_prompt', type=str, help='uc prompt')
@click.option('--width', required=True, type=int, help='width')
@click.option('--height', required=True, type=int, help='height')
@click.option('--init_image_url', type=str, help='init image url')
@click.option('--init_image_similarity', type=int, default=50, help='init image similarity')
@click.option('--num', type=int, default=1, help='number')
@click.option('--art_genre', type=str, help='art genre')
@click.option('--seed', type=str, help='seed')
def calc_cost(style_id, prompt, uc_prompt, width, height, init_image_url, init_image_similarity, mask_zone_image_url,
              num, art_genre, steps, cfg_scale, sampler_name, seed):
    req = {
        "style_id": style_id,
        "prompt": prompt,
        "uc_prompt": uc_prompt,
        "width": width,
        "height": height,
        "init_image_url": init_image_url,
        "init_image_similarity": init_image_similarity,
        "mask_zone_image_url": mask_zone_image_url,
        "num": num,
        "art_genre": art_genre,
        "seed": seed
    }
    resp = post_requests(open_url + '/calc-cost', get_headers(), req)
    click.echo(json.dumps(resp))


# 获取上传底图的签名凭证
@click.command()
@click.option('--file_name', required=True, type=str, help='file name')
def create_upload_token(file_name):
    params = f"?file_name={file_name}"
    resp = get_requests(open_url + '/create-upload-token' + params, get_headers())
    click.echo(json.dumps(resp))


# 获取上传底图的签名凭证
@click.command()
def balance():
    resp = get_requests(open_url + '/balance', get_headers())
    click.echo(json.dumps(resp))


# 超分
@click.command()
@click.option('--job', required=True, type=str, help='job')
def upscale(job):
    req = {
        "job": job
    }
    resp = post_requests(open_url + '/upscale', get_headers(), req)
    click.echo(json.dumps(resp))


# 超分结果查询
@click.command()
@click.option('--jobs', required=True, type=str, help='jobs')
def upscale_result(jobs):
    req = {
        "jobs": jobs.split(',')
    }
    resp = post_requests(open_url + '/upscale-result', get_headers(), req)
    click.echo(json.dumps(resp))


# 上传图片到oss
@click.command()
@click.option('--sign_url', required=True, type=str, help='sign_url')
@click.option('--file', required=True, type=str, help='file path')
def upload(sign_url, file):
    with open(file, 'rb') as f:
        resp = requests.put(sign_url, f)
        if resp.status_code != 200:
            click.echo(f"status code: {resp.status_code}, error: {resp.text}")
            return

    idx = sign_url.index("?Expires=")
    click.echo(sign_url[:idx])


cli.add_command(generate_key)
cli.add_command(set_appid)
cli.add_command(sign)
cli.add_command(style_base_infos)
cli.add_command(style_resource)
cli.add_command(txt2img)
cli.add_command(img2img)
cli.add_command(generate_result)
cli.add_command(cancel)
cli.add_command(calc_cost)
cli.add_command(create_upload_token)
cli.add_command(balance)
cli.add_command(upscale)
cli.add_command(upscale_result)
cli.add_command(upload)

if __name__ == "__main__":
    cli()
