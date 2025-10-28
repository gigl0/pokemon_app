from fastapi import FastAPI, HTTPException
import requests, json, os

POKEAPI = "https://pokeapi.co/api/v2/pokemon-species?limit=20000"
CACHE_FILE = "pokemon_cache.json"

app = FastAPI(title="Pokédex Antecedente API")

# ===== FUNZIONI DI SUPPORTO =====
def load_pokemon_map():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            print("🔁 Cache Pokémon caricata.")
            return json.load(f)

    print("⏳ Scaricamento elenco Pokémon dal Pokédex nazionale...")
    resp = requests.get(POKEAPI)
    if resp.status_code != 200:
        raise Exception("Errore nel download dei dati dalla PokéAPI")

    species_list = resp.json()["results"]
    name_to_number = {}
    number_to_name = {}

    for i, species in enumerate(species_list, start=1):
        name = species["name"]
        name_to_number[name] = i
        number_to_name[i] = name

    data = {"name_to_number": name_to_number, "number_to_name": number_to_name}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ Cache salvata in pokemon_cache.json")
    return data

def get_antecedente(pokemon_name: str, mapping: dict):
    pokemon_name = pokemon_name.lower().strip().replace(" ", "-")
    name_to_number = mapping["name_to_number"]
    number_to_name = mapping["number_to_name"]

    if pokemon_name not in name_to_number:
        raise HTTPException(status_code=404, detail=f"Pokémon '{pokemon_name}' non trovato.")

    num = name_to_number[pokemon_name]
    if num == 1:
        return {"pokemon": pokemon_name, "number": 1, "antecedente": None, "message": "È il primo Pokémon (#001)."}

    prev_name = number_to_name.get(num - 1, None)
    return {
        "pokemon": pokemon_name,
        "number": num,
        "antecedente": prev_name,
        "antecedente_number": num - 1
    }

def get_successore(pokemon_name: str, mapping: dict):
    pokemon_name = pokemon_name.lower().strip().replace(" ", "-")
    name_to_number = mapping["name_to_number"]
    number_to_name = mapping["number_to_name"]

    if pokemon_name not in name_to_number:
        raise HTTPException(status_code=404, detail=f"Pokémon '{pokemon_name}' non trovato.")

    num = name_to_number[pokemon_name]
    if num == len(number_to_name):
        return {"pokemon": pokemon_name, "number": num, "successore": None, "message": "È l'ultimo Pokémon nel Pokédex."}

    next_name = number_to_name.get(num + 1, None)
    return {
        "pokemon": pokemon_name,
        "number": num,
        "successore": next_name,
        "successore_number": num + 1
    }

# ===== AVVIO E ENDPOINTS =====
pokemon_map = load_pokemon_map()

@app.get("/")
def root():
    return {"message": "Benvenuto nell'API Pokédex Antecedente!"}

@app.get("/antecedente/{pokemon_name}")
def antecedente(pokemon_name: str):
    return get_antecedente(pokemon_name, pokemon_map)

@app.get("/successore/{pokemon_name}")
def successore(pokemon_name: str):
    return get_successore(pokemon_name, pokemon_map)
