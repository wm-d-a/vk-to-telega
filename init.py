import pickle

f = open('log.txt', 'w')
f.close()
data = {}
with open('users.pickle', 'wb') as f:
    pickle.dump(data, f)
f = open('users.pickle', 'wb')
f.close()
