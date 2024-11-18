from PIL import Image 
import requests 
from transformers import AutoModelForCausalLM , AutoTokenizer, AutoProcessor
from transformers import BitsAndBytesConfig


quantization_config = BitsAndBytesConfig(load_in_4bit=True)

model_id = "microsoft/Phi-3-vision-128k-instruct" 

model = AutoModelForCausalLM.from_pretrained(model_id, 
                                            device_map="cuda", 
                                            trust_remote_code=True, 
                                            torch_dtype="auto", 
                                            quantization_config = quantization_config,  
                                            _attn_implementation='flash_attention_2') 

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True) 

messages = [ 
    {
        "role": "system",
        "content": "You are provided with an image which shows a symbol in green box, analyse the image and answer the questions",
    },
    {
        "role": "user", 
        "content": "<|image_1|>\n What is the name of the symbol shown in blue box?"
    } 
] 

 
image = Image.open("symbol.png")
prompt = processor.tokenizer.apply_chat_template(messages, 
                                                 tokenize=False, 
                                                 add_generation_prompt=True)
inputs = processor(prompt, [image], return_tensors="pt").to("cuda:0") 

generation_args = { 
    "max_new_tokens": 500, 
    "temperature": 0.01, 
    "do_sample": False, 
} 

generate_ids = model.generate(**inputs, eos_token_id=processor.tokenizer.eos_token_id, **generation_args) 

generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
response = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0] 
print(100*"-")
print(100*"-")
print(100*"-")
print(response)
