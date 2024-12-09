import chromadb
import config, json, uuid

def train():
    client = chromadb.PersistentClient(path="./store/hiketron")
    collection = client.get_or_create_collection(name="website")
    with open('./data/products.json', 'r') as file:
        products = json.load(file)

    for product in products:
        collection.add(
            documents=[json.dumps(product)],
            metadatas=[{"type": "products", "is_active": True}],
            ids=[str(uuid.uuid4())]
        )
    print(f"Loaded {len(products)} products into ChromDB.")

if __name__ == "__main__":
    train()