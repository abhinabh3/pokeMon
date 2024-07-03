from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
import requests
import gunicorn
import psycopg2

app = Flask(__name__)

# Load configuration from a config file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pokemon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Defining the Pokemon model
class Pokemon(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    image: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(100))

# Ensuring that we are running within the Flask application context
with app.app_context():

    db.create_all()


    if not db.session.query(Pokemon).first():
        url = "https://pokeapi.co/api/v2/pokemon?limit=100"
        response = requests.get(url)
        if response.status_code == 200:
            pokemon_list = response.json()['results']
            for pokemon in pokemon_list:
                pokemon_url = pokemon['url']
                response = requests.get(pokemon_url)
                if response.status_code == 200:
                    data = response.json()
                    name = data['name']
                    image_url = data['sprites']['front_default']
                    types = ', '.join([t['type']['name'] for t in data['types']])

                    new_pokemon = Pokemon(
                        name=name,
                        image=image_url,
                        type=types
                    )
                    db.session.add(new_pokemon)
            db.session.commit()

# Defining API routes
@app.route('/api/v3/pokemons', methods=['GET'])
def get_pokemons():
    name = request.args.get('name')
    type_ = request.args.get('type')

    query = db.session.query(Pokemon)

    if name:
        query = query.filter(Pokemon.name.ilike(f'%{name}%'))
    if type_:
        query = query.filter(Pokemon.type.ilike(f'%{type_}%'))

    pokemons = query.all()
    pokemon_list = []
    for pokemon in pokemons:
        pokemon_data = {
            'name': pokemon.name,
            'image': pokemon.image,
            'type': pokemon.type
        }
        pokemon_list.append(pokemon_data)

    return jsonify(pokemon_list)

if __name__ == '__main__':
    app.run(debug=True)
