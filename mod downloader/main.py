from pocketbase import PocketBase
import requests, os

DEBUG = True
DB_URL = "https://moddown.thelocal.cf" if not DEBUG else "http://127.0.0.1:8090"
SFS_PATH = "C:/Program Files (x86)/Steam/steamapps/common/Spaceflight Simulator/Spaceflight Simulator Game"

client = PocketBase(DB_URL)


def save_mod(record):
    print(f"Downloading: '{record.filename}'")
    mod = requests.get(client.get_file_url(record, record.file, {}))
    print("Saving...")
    with open(os.path.join(SFS_PATH, "Mods", record.filename), "wb") as f:
        f.write(mod.content)
    print("Saved!")
    for dependency_id in record.dependencies:
        dependency = client.collection("mod_version").get_one(dependency_id)
        dep_mod = client.collection("mods").get_one(dependency.mod)
        print(f"Found dependency: {dep_mod.mod_name}")
        save_mod(dependency)


mods = (
    client.collection("mods")
    .get_list(query_params={"sort": "-mod_name", "filter": 'type = "mod"'})
    .items
)
for mod in mods:
    print(mod.mod_name)
    print(mod.description)
    print("Latest:")
    versions = (
        client.collection("mod_version")
        .get_list(query_params={"filter": 'mod = "' + mod.id + '"', "sort": "-version"})
        .items
    )
    try:
        latest = versions.pop(0)
    except IndexError:
        print("No version(s) available")
        print("-" * 20)
        continue
    print(latest.version + " - " + client.get_file_url(latest, latest.file, {}))
    print("Other")
    for version in versions:
        print(version.version + " - " + version.file)
    print("Downloading latest...")
    save_mod(latest)
    print("-" * 20)
