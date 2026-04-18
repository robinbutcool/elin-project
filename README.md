![Screenshot_2026-04-13-00-37-31-82_84c9ef400ab248a2e4a3b31139e21163](https://github.com/user-attachments/assets/19bb500c-4081-432b-bfa7-8e6dc9a0977f)

# The elin project

The elin project provides a local and free assistant for coding, talking and help with Linux. 

It has multiple options such as:

- Standard(runs on most modern hardware)

- Unfiltered(same size as standard but abliterated)

- Lite(smaller than standard, focused for slower hardware or faster responses on modern hardware)

- Cloud(runs via the groq API, good for super bad hardware or smarter models in trade with not being local/not private)

Look below for further info.

# THANK YOU!
First of all, lets thank the ones who brought me to this:
- Claude. Banned me for not being 18, appreciate the "support" 🥴

Seriously now, thanks to @alevio_life on tiktok! His project was a HUGE inspiration to elin.

The models are also not mine, you can find the hugginface repos in the launch file of each!

# INSTALLATION

**Important Note:** This project is linux focused, it may work on MacOS but i recommend using @alevio_life's since he tested it on MacOS and created it for MacOS.

You need following things:
```bash
docker docker-compose python python-annotated-types python-cffi python-datasets python-fastapi python-gitpython python-huggingface-hub python-jinja python-matplotlib python-numpy python-openai python-packaging python-pandas python-pydantic python-pytest python-pyyaml python-requests python-safetensors python-seaborn python-sentencepiece python-tabulate python-tabulate python-pytorch python-tqdm python-typer python-typing_extensions pyside6 uvicorn
```
Install them with your package manager and then just run the file you want to.


Clone this repo and the needed files:
```bash
git clone https://github.com/quinnyfoco-design/elin-project
```

# HARDWARE NEEDED

For the standard and unfiltered model, any modern gpu with 8GB vRAM is enough. 6GB vRAM GPU's will need offloading, which also makes it slower.

For the lite model, a GPU with ~4GB vRAM is good, 2GB vRAM will also need a bit of offloading and will be slower.

For the Cloud model, you dont need any good hardware at all just follow the tutorial(this runs on android phones, super bad desktop hardware, more, not local or private though).
