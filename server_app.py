from server.facade import ServerFacade

def main():
    # Iniciamos el servidor en el puerto 5000
    ServerFacade(port=5000).run()

if __name__ == "__main__":
    main()
