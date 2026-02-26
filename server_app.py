from server.facade import ServerFacade
from dep_checker import bootstrap

def main():
    bootstrap("servidor")
    # Iniciamos el servidor en el puerto 5000
    ServerFacade().run()

if __name__ == "__main__":
    main()
