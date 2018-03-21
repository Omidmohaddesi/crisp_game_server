""" Server builds a flask server to provide APIs for the game """

from flask import Flask, send_from_directory
from flask import request
from flask_restful import Resource, Api
from flask import jsonify
from flask import abort
from hashids import Hashids
import uuid
import jwt
import datetime
import os

from game import build_game
from graph import graph
from simulation_builder import build_simulation
from simulator import agent

path = os.path.join(os.path.abspath('..'), 'client/')

app = Flask(__name__, static_url_path='', static_folder=path)
api = Api(app)
hashids = Hashids(salt="Drug Shortage")

game_count = 0
games = {}
hash_id_to_game_map = {}
parameters = []
players = {'id0': 0}
decisions = []


@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Origin',
        'http://www.neumadscience.com')
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


@app.route('/api/create_game', methods=['GET'])
def new_game():
    """ respond to the request from the client to create a new game """

    user_id = request.args.get('user_id')
    game_id = request.args.get('game_id')
    start_week = request.args.get('start_week')
    role = request.args.get('role')

    global game_count
    game_count = game_count + 1
    game = build_game()
    games[game_id] = game
    hash_id = hashids.encode(game_count)
    game.hash_id = hash_id
    hash_id_to_game_map[hash_id] = game

    # TODO (Yifan): Fast forward the game to the starting week
    # TODO (Yifan): Associate the player with a certain game agent

    token_payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=0),
        'iat': datetime.datetime.utcnow(),
        'game_id': game_id,
        'user_id': user_id
    }

    return jsonify({
        'token': jwt.encode(token_payload, 'SECRET_KEY'),
        'hash_id': hash_id,
    })


@app.route('/api/get_game_param', methods=['GET'])
def get_game_param():
    """ respond the request of querying the value of a simulation parameter. """

    token = request.args.get('token')
    cycle = int(request.args.get('cycle'))
    agent_id = int(request.args.get('agentId'))
    param = request.args.get('paramName')

    token_payload = jwt.decode(token, 'SECRET_KEY')

    game_id = token_payload['game_id']
    print cycle, agent_id, param, game_id
    game = games[game_id]
    if game == None:
        abort(404)

    agent = game.simulation.agents[agent_id]
    if agent == None:
        abort(404)

    if not agent.is_history_available(cycle):
        abort (404)

    history = agent.get_history_item(cycle)

    try:
        if param == "inventory":
            value = history.inventory
        elif param == "urgent":
            if not isinstance(agent, agent.HealthCenter):
                abort (400)
            value = history.patient[0]
        elif param == "urgent":
            if not isinstance(agent, agent.HealthCenter):
                abort (400)
            value = history.patient[1]
        else:
            raise ValueError("Not supported paramter type")
    except Exception as e:
        print e
        abort(400)

    return str(value)

    # user_id = token_payload['user_id']



    # value = 0
    # if param == 'week':
    #     value = game.simulation.now
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['week'] = value

    # if param == 'inventory':
    #     value = game.simulation.health_centers[0].inventory_level()
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['inventory'] = value

    # if param == 'urgent':
    #     value = game.simulation.health_centers[0].urgent
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['urgent'] = value

    # if param == 'non_urgent':
    #     value = game.simulation.health_centers[0].non_urgent
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['non_urgent'] = value

    # if param == 'on_order_DS1':
    #     # on_order = game.simulation.health_centers[0].on_order()
    #     # value = sum(i['amount'] for i in on_order if i['destination'] == 2)

    #     value = sum(
    #         game.simulation.health_centers[0].on_order[j].amount
    #         for j in range(
    #             0, len(game.simulation.health_centers[0].on_order))
    #         if game.simulation.health_centers[0].on_order[j].dst.id == 2)
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['on_order_DS1'] = value

    # if param == 'on_order_DS2':
    #     # on_order = game.simulation.health_centers[0].on_order()
    #     # value = sum(i['amount'] for i in on_order if i['destination'] == 3)
    #     value = sum(
    #         game.simulation.health_centers[0].on_order[j].amount
    #         for j in range(
    #             0, len(game.simulation.health_centers[0].on_order))
    #         if game.simulation.health_centers[0].on_order[j].dst.id == 3)
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['on_order_DS2'] = value

    # if param == 'received_DS1':
    #     # delivery = game.simulation.health_centers[0].delivery()
    #     # value = sum(i["item"]["amount"] for i in delivery if i["src"] == 2)
    #     value = sum(
    #         game.simulation.health_centers[0].get_history_item(
    #             game.simulation.now)['delivery'][j]["item"].amount for j in range(
    #             0, len(
    #                 game.simulation.health_centers[0].get_history_item(
    #                     game.simulation.now)['delivery'])) if game.simulation.health_centers[0].get_history_item(
    #                     game.simulation.now)['delivery'][j]["src"].id == 2)
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['received_DS1'] = value

    # if param == 'received_DS2':
    #     # delivery = game.simulation.health_centers[0].delivery()
    #     # value = sum(i["item"]["amount"] for i in delivery if i["src"] == 3)
    #     value = sum(
    #         game.simulation.health_centers[0].get_history_item(
    #             game.simulation.now)['delivery'][j]["item"].amount for j in range(
    #             0, len(
    #                 game.simulation.health_centers[0].get_history_item(
    #                     game.simulation.now)['delivery'])) if game.simulation.health_centers[0].get_history_item(
    #                     game.simulation.now)['delivery'][j]["src"].id == 3)
    #     for i in parameters:
    #         if i['user_id'] == user_id:
    #             i['received_DS2'] = value

    return str(value)


class Decision(Resource):
    @app.route('/api/make_decision', methods=['POST'])
    def make_decision(self):
        ''' respond the request of posting the value of a decision parameters. '''

        token = request.args.get('token')
        token_payload = jwt.decode(token, 'SECRET_KEY')

        game_id = token_payload['game_id']
        game = games[game_id]

        user_id = token_payload['user_id']

        decision_name = request.args.get('decision_name')
        decision_value = request.args.get('decision_value')

        if decision_name == 'order_type':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['order_type'] = decision_value

        if decision_name == 'allocation_type':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['allocation_type'] = decision_value

        if decision_name == 'satisfied_urgent':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['satisfied_urgent'] = decision_value

        if decision_name == 'satisfied_non_urgent':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['satisfied_non_urgent'] = decision_value

        if decision_name == 'order_amount_DS1':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['order_amount_DS1'] = decision_value

        if decision_name == 'order_amount_DS2':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['order_amount_DS2'] = decision_value

        if decision_name == 'order_amount_total':
            for i in decisions:
                if i['user_id'] == user_id:
                    i['order_amount_total'] = decision_value

        return str(decision_value)


@app.route("/api/get_user_id")
def id_generator():
    """ respond the request from the client to generate a unique user_id """

    user_id = str(uuid.uuid4())
    player_id = int(list(players)[-1].lstrip('id')) + 1
    player_id = 'id%i' % player_id
    players[player_id] = user_id

    return players[player_id]


@app.route('/api/next_cycle', methods=['GET', 'POST'])
def next_cycle():
    """ respond the request of moving the simulation to the next cycle. """

    token = request.args.get('token')
    token_payload = jwt.decode(token, 'SECRET_KEY')

    game_id = token_payload['game_id']
    game = games[game_id]

    # game.get_current_history_item(game, now=1)

    game.runner.next_cycle()

    # simulation = game.simulation
    #
    # decision_maker = dmaker.PerAgentDecisionMaker()
    #
    # runner = sim_runner.SimulationRunner(simulation, decision_maker)
    # runner.next_cycle()
    week = game.simulation.now
    return str(week)


@app.route("/api/update_graphs", methods=['GET'])
def update():
    ''' updates graphs' images for the gamettes for each player. '''

    token = request.args.get('token')
    token_payload = jwt.decode(token, 'SECRET_KEY')

    game_id = token_payload['game_id']
    game = games[game_id]

    user_id = token_payload['user_id']

    graph(game, path, user_id=user_id)

    return "updated!"


@app.route('/Charts/<filename>')
def send_image(filename):
    return send_from_directory(app.static_folder, filename)


api.add_resource(Decision, '/api/make_decision')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
