import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

# Load model and tokenizer
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"  # Requires HF access
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    load_in_8bit=True,  # For memory efficiency
)

# Prepare for LoRA
model = prepare_model_for_kbit_training(model)
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # Llama attention layers
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# Load dataset
dataset = load_dataset("json", data_files="destiny_dataset.jsonl", split="train")

def tokenize_function(examples):
    combined = [f"{inp}\n{out}" for inp, out in zip(examples["input"], examples["output"])]
    model_inputs = tokenizer(combined, max_length=512, truncation=True, padding="max_length")
    model_inputs["labels"] = model_inputs["input_ids"].copy()
    return model_inputs

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Training
training_args = TrainingArguments(
    output_dir="./llama-destiny-finetuned",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    save_steps=500,
    logging_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)
trainer.train()

# Save LoRA adapters
model.save_pretrained("./llama-destiny-lora")
tokenizer.save_pretrained("./llama-destiny-lora")