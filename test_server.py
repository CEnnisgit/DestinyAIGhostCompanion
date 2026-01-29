from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def root():
    return {'message': 'Hello World'}

@app.post('/chat')
def chat():
    return {'reply': 'Test response'}
