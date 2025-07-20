"""

🧾 Summary – What this script does (in 3 sentences):
The script initializes a Ray _qfn_cluster_node and starts the Ray Serve system, then fetches GitHub credentials and repository information from an authenticated external API.

It clones or downloads required worker repositories (including _utils and a main worker), dynamically loads their Python modules, and scans for instantiable classes in head.py.

Based on the detected class type (Ray actor or Serve deployment), it either deploys the class using serve.run() or starts it as a Ray actor via .remote(), with logs and error handling throughout the process.


USER_ID
ENV_ID
DEPLOYMENT_TYPE
REQUEST_ENDPOINT
DOMAIN
"""

import importlib

import subprocess

from ray import serve
import importlib.util
import inspect
import ray, os, sys


init_state = os.environ.get("INIT")


def set_endpoint():
    import socket
    env_id = os.environ.get("ENV_ID")

    host_ip = socket.gethostbyname(socket.gethostname())
    address = f"ray://{host_ip}:10001"
    endpoint = address + f"/{env_id}"
    os.environ["IP"] = endpoint


if os.name == "nt":
    from utils.logger import LOGGER




def clone_repo(git_url):
    # Wenn noch nicht geklont → klonen
    try:
        print("📥 Klone GitHub-Repo...")
        subprocess.run(["git", "clone", git_url], check=True)
    except Exception as e:
        print("Couldnt clone repo:", e)


def clone_process(worker_repo):
    # check clone repos
    for repo in [worker_repo, "_utils"]:
        REMOTE_URL = f"https://{token}@github.com/{user}/{repo}/archive/master.zip"
        clone_repo(REMOTE_URL)

        if repo not in sys.path:
            # Importpfade einfügen
            globals()[repo] = importlib.import_module(repo)



def get_instantiable_classes(file_path):
    module_name = file_path.split("/")[-1].replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    instantiable = []
    for name, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ != module_name:
            continue
        try:
            cls()  # versuchen zu instanziieren ohne Argumente
            instantiable.append(cls)
        except:
            continue  # überspringe Klassen mit __init__(args)

    return instantiable


def start_worker_class(worker_repo, worker_type="remote"):
    file = os.path.join(f"{worker_repo}", "main.py")
    classes = get_instantiable_classes(file)
    for cls in classes:
        try:
            if worker_type=="remote":
                instance = cls.remote()
                if hasattr(instance, "run"):
                    print("→ Ergebnis:", ray.get(instance.run.remote()))
            elif worker_type=="deployment":
                serve.run(
                    cls.bind(),
                    route_prefix="/"
                )
            print(f"✅ Klasse gestartet: {cls.__name__}")
            break  # optional: nur den ersten nehmen
        except Exception as e:
            print(f"❌ {cls.__name__} konnte nicht gestartet werden: {e}")



if __name__ == "__main__":
    # run
    try:
        #ray.init()
        #serve.start(detached=True)

        if init_state is True or init_state == "True":
            worker_repo, user, token = get_gh_creds()
            if worker_repo is None:
                print("❌ Zugriff verweigert.")
                ray.shutdown()
                # stop program
                exit(1)

            clone_process(worker_repo)

            globals()["_server"].ServerWorker.remote()

            start_worker_class(
                worker_repo, worker_type="remote" if "server" not in worker_repo else "deployment"
            )
            os.environ["INIT"] = "False"

        LOGGER.info("server started")
    except Exception as e:
        LOGGER.error(f"server error: {e}")
        LOGGER.info("stopping program...")
        ray.shutdown()
        exit(1)
