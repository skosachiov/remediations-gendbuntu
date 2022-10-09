import os

for root, dirs, files in os.walk("."):
    for name in dirs:
        path = os.path.join(root, name)
        if ".git/" in path: continue
        if not os.listdir(path):
            print("touch " + path + "/.gitignore")
            os.system("touch " + path + "/.gitignore")
