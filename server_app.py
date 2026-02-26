from server.facade import ServerFacade

def main():
    # Iniciamos el servidor en el puerto 5000
    ServerFacade().run()

if __name__ == "__main__":
    main()
