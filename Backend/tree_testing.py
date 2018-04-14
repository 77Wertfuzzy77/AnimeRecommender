Testing = {
	"Action" : {
		"VALUE" : [9, 8, 7, 6],
		"Romance" : {
			"VALUE" : [9, 7, 6],
			"Sci-Fi" : {
				"VALUE" : [7]
			},
			"Comedy" : {
				"VALUE" : [6]
			}
		},
		"Comedy" : {
			"VALUE" : [6],
			"Romance" : {
				"VALUE" : [6]
			}
		}
	}
}

# Animes 
# Action : 8
# Action, Romance : 9
# Action, Comedy, Romance : 6
# Action, Romance, Sci-Fi : 7


def update_tree(tree, keys, value):
	for key in keys:
		new_keys = list(keys)
		new_keys.remove(key)
		if key in tree:
			if len(keys) == 1:
				tree[key]['VALUE'] = tree[key]['VALUE'] + [value]
			else:
				tree[key]['VALUE'] = tree[key]['VALUE'] + [value]
				tree[key] = update_tree(tree[key], new_keys, value)
		else:
			tree[key] = {}
			tree[key]['VALUE'] = [value]
			if len(keys) == 1:
				pass
			else:
				tree[key] = update_tree(tree[key], new_keys, value)
	return tree

Tree = {}

Animes = [
	[8, 'Action'],
	[9, 'Action', 'Romance'],
	[6, 'Action', 'Comedy', 'Romance'],
	[7, 'Action', 'Romance', 'Sci-Fi']
	]

for anime in Animes:
	Tree = update_tree(Tree, anime[1:], anime[0])