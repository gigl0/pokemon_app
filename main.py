from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests, json, os

API = "https://pokeapi.co/api/v2"
CACHE_FILE = "pokemon_cache.json"

app = FastAPI(title="Pokédex Antecedente API")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
def serve_home():
    return FileResponse("static/index.html")

def load_pokemon_map():
    # Se esiste la cache, caricala e normalizza le chiavi di number_to_name a int
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalizza chiavi -> int (importantissimo)
        data["number_to_name"] = {int(k): v for k, v in data["number_to_name"].items()}
        return data

    # Altrimenti crea la cache in modo “veloce”: usa l’ordine restituito da /pokemon-species
    # (per la serie principale coincide col National Dex).
    resp = requests.get(f"{API}/pokemon-species?limit=20000")
    if resp.status_code != 200:
        raise RuntimeError("Errore nel download dei dati da PokéAPI")
    species_list = resp.json()["results"]

    name_to_number = {}
    number_to_name = {}
    for i, sp in enumerate(species_list, start=1):
        name = sp["name"]
        name_to_number[name] = i
        number_to_name[i] = name

    data = {"name_to_number": name_to_number, "number_to_name": number_to_name}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

pokemon_map = load_pokemon_map()

def get_name_by_number(n: int, mapping: dict) -> str | None:
    """Torna il nome dal mapping; se manca, fa fallback a PokéAPI e aggiorna la cache in RAM."""
    number_to_name = mapping["number_to_name"]
    name = number_to_name.get(n)
    if name:
        return name
    # Fallback robusto
    r = requests.get(f"{API}/pokemon-species/{n}")
    if r.status_code != 200:
        return None
    name = r.json()["name"]
    number_to_name[n] = name  # aggiorna in RAM per le prossime volte
    return name

def normalize_name(s: str) -> str:
    s = s.strip().lower().replace(" ", "-")
    s = s.replace("mr. mime", "mr-mime").replace("farfetch’d", "farfetchd").replace("farfetch'd", "farfetchd")
    s = s.replace("nidoran♀", "nidoran-f").replace("nidoran♂", "nidoran-m")
    return s

@app.get("/antecedente/{pokemon_name}")
def antecedente(pokemon_name: str):
    name_to_number = pokemon_map["name_to_number"]
    pokemon_name = normalize_name(pokemon_name)
    if pokemon_name not in name_to_number:
        raise HTTPException(status_code=404, detail=f"Pokémon '{pokemon_name}' non trovato.")

    num = name_to_number[pokemon_name]
    sprite_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{num}.png"

    if num == 1:
        return {
            "pokemon": pokemon_name,
            "number": num,
            "sprite": sprite_url,
            "antecedente": None,
            "message": "È il primo Pokémon (#001)."
        }

    prev_num = num - 1
    prev_name = get_name_by_number(prev_num, pokemon_map)

    return {
        "pokemon": pokemon_name,
        "number": num,
        "sprite": sprite_url,
        "antecedente": prev_name,
        "antecedente_number": prev_num
    }

