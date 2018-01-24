import os
import sys
import json
import requests
import time
import datetime

def post_lichess_api(url, data):
    time.sleep(2)
    while True:
        r = requests.post(url, data)
        if r.status_code == 200:
            break
        elif r.status_code == 429:
            print('Rate-limited. Sleeping for 1min')
            time.sleep(60)
        else:
            break
    return r.json()

def node(g, spec):
    parts = spec.split('.')
    for p in parts:
        if p not in g:
            return None
        g = g[p]
    return str(g)

def cap(s):
    if len(s) == 0:
        return s
    return s[0].upper() + s[1:]

def game_to_pgn(p, g):
    result = '1/2-1/2' if node(g, 'status') == 'draw' else '1-0' if node(g, 'winner') == 'white' else '0-1' if node(g, 'winner') == 'black' else '*'
    headers = []
    headers.append(('Event', '%s - %s' % (p['league'], p['season'])))
    headers.append(('Site', g['url']))
    headers.append(('Date', datetime.datetime.fromtimestamp(int(g['createdAt']) / 1000.0).strftime('%Y.%m.%d')))
    headers.append(('Round', p['round']))
    headers.append(('White', node(g, 'players.white.userId')))
    headers.append(('Black', node(g, 'players.black.userId')))
    headers.append(('Result', result))
    headers.append(('WhiteElo', node(g, 'players.white.rating')))
    headers.append(('BlackElo', node(g, 'players.black.rating')))
    headers.append(('ECO', node(g, 'opening.eco')))
    headers.append(('Opening', node(g, 'opening.name')))
    headers.append(('Variant', cap(g['variant'])))
    headers.append(('TimeControl', node(g, 'clock.initial') + '+' + node(g, 'clock.increment')))
    moves = g['moves']
    pgn = ''
    for h in headers:
        if h[1] is None:
            pgn += '[%s "?"]\n' % (h[0])
        else:
            pgn += '[%s "%s"]\n' % h
    pgn += '\n'
    ply = 0
    for m in moves.split(' '):
        if ply % 2 == 0:
            pgn += str(int(ply / 2 + 1)) + '. '
        pgn += m + ' '
        ply += 1
    pgn += result
    return pgn

def download_games(league_tag, season_tag):
    r = requests.get('https://www.lichess4545.com/api/get_season_games/?league=%s&season=%s' % (league_tag, season_tag))
    games = r.json()['games']
    return zip(games, enumerate_lichess_games([g['game_id'] for g in games]))

def enumerate_lichess_games(game_ids):
    url = 'https://lichess.org/api/games?with_moves=1'
    while len(game_ids) > 0:
        batch = game_ids[:300]
        result = post_lichess_api(url, data=','.join(batch))
        for g in result:
            yield g
        game_ids = game_ids[300:]

def save_pgn(filename, games):
    with open(filename, 'wb') as file:
        for league_game, lichess_game in games:
            pgn = game_to_pgn(league_game, lichess_game)
            file.write((pgn + '\n\n').encode('utf-8'))

if __name__ == '__main__':
    league = input('League tag: ')
    season = input('Season tag: ')

    games = download_games(league, season)
    
    pgn_name = '%s-s%s.pgn' % (league, season)
    save_pgn(pgn_name, games)
