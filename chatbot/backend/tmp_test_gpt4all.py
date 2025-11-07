from gpt4all import GPT4All
import traceback

try:
    print('Instanciando GPT4All...')
    m = GPT4All('orca-mini-3b-gguf2-q4_0.gguf')
    print('Instancia creada:', type(m))
except Exception as e:
    traceback.print_exc()
    print('\nError:', e)
