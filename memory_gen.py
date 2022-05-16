import requests, os, time

API_URL = "https://api-inference.huggingface.co/models/slauw87/bart_summarisation"
headers = {"Authorization": os.getenv("HUG_API")}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def memory_gen(context):
    out = query({
        "inputs": context,
    })
    if type(out) != list:
        if 'error' in out.keys():
            if out['error'] == 'Model slauw87/bart_summarisation is currently loading':
                time.sleep(out['estimated_time']+1)
                out = query({
                    "inputs": context,
                })
            else:
                raise Exception
    return out[0]['summary_text']