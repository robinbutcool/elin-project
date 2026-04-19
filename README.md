<img width="416" height="310" alt="2158" src="https://github.com/user-attachments/assets/601c3de0-da52-44ba-8ea3-1c3c6f7b245c" />

# The elin ~~project~~ fork

The elin project provides a local and free assistant for coding, talking and help with Linux. It has memory saving. To turn off autoload its --no-memory.

It has multiple options such as:

- Standard(runs on most modern hardware)

- Unfiltered(same size as standard but abliterated)

- Lite(smaller than standard, focused for slower hardware or faster responses on modern hardware)

- Cloud(runs via the groq API, good for super bad hardware or smarter models in trade with not being local/not private)

Look below for further info.

# THANK YOU!
First of all, lets thank the ones who brought me to this:
- germanphoneguy on tiktok (literally the guy that made the original project)

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
one last thing:
to get searxng to work you need to do this.

```bash
bash -c 'cat <<EOF > .env
                        # SearXNG settings
                        SEARXNG_VERSION=latest
                        SEARXNG_PORT=8080
                        SEARXNG_HOSTNAME=localhost
                        SEARXNG_SECRET_KEY=$(openssl rand -hex 32)
                        EOF'
```
# HARDWARE NEEDED

For the standard and unfiltered model, any modern gpu with 8GB vRAM is enough. 6GB vRAM GPU's will need offloading, which also makes it slower.

For the lite model, a GPU with ~4GB vRAM is good, 2GB vRAM will also need a bit of offloading and will be slower.

For the Cloud model, you dont need any good hardware at all just follow the tutorial(this runs on android phones, super bad desktop hardware, more, not local or private though).
