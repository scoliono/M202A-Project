from wifi import connect_to_wifi

def main():
    print("Starting connect_to_wifi")
    connect_to_wifi("rpi1", "password")

if __name__ == "__main__":
    main()