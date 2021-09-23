import pickle

f = open('log.txt', 'w')
f.close()
data = {}
f = open('users.pickle', 'wb')
f.close()
with open('users.pickle', 'wb') as f:
    pickle.dump(data, f)
