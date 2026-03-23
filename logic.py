import os
import json
import requests
import re

CONFIG_FILE = 'config.json'


def load_config():
    default_config = {
        "user_dir": "",
        "server_ip": "127.0.0.1",
        "server_port": "25565",
        "server_path": "/",
        "confirm_delete": True,
        "copy_missing": True
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for k, v in default_config.items():
                    config.setdefault(k, v)
                return config
        except Exception:
            return default_config

    return default_config


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_files_in_dir(directory):
    if not os.path.exists(directory):
        return set()
    return {f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))}


def build_url(ip, port, path):
    if not path or path == "/":
        return f"http://{ip}:{port}"
    clean_path = path.strip('/')
    return f"http://{ip}:{port}/{clean_path}"


def test_connection(ip, port, path):
    url = build_url(ip, port, path)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            return True, "Сервер доступен (режим файлового списка)"
        elif "application/json" in content_type:
            return True, "Сервер доступен (JSON API)"
        else:
            return True, "Сервер отвечает (неизвестный формат)"

    except requests.exceptions.Timeout:
        return False, "Таймаут"
    except requests.exceptions.ConnectionError:
        return False, "Нет соединения"
    except Exception as e:
        return False, str(e)


def get_server_mods(ip, port, path):
    url = build_url(ip, port, path)

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        data = response.json()
        if isinstance(data, list):
            return set(data)
        elif isinstance(data, dict) and "mods" in data:
            return set(data["mods"])

    text = response.text

    files = set(re.findall(r'href="([^"]+)"', text))

    files = {f for f in files if not f.endswith("/")}

    return files


def compare_mods(user_dir, server_mods):
    user_mods = get_files_in_dir(user_dir)
    extra = list(user_mods - server_mods)
    missing = list(server_mods - user_mods)
    return extra, missing


def delete_mod(user_dir, mod_name):
    try:
        os.remove(os.path.join(user_dir, mod_name))
        return True, f"Удален: {mod_name}"
    except Exception as e:
        return False, f"Ошибка удаления {mod_name}: {e}"


def download_mod(ip, port, path, mod_name, user_dir):
    url = f"{build_url(ip, port, path)}/{mod_name}"
    dest = os.path.join(user_dir, mod_name)

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(dest, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        return True, f"Скачан: {mod_name}"

    except Exception as e:
        return False, f"Ошибка скачивания {mod_name}: {e}"