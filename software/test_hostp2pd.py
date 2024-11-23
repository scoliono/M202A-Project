

from hostp2pd import HostP2pD
import time

def main():
    # Create an instance of HostP2pD
    hostp2pd = HostP2pD(
        config_file="hostp2pd.yaml",
        interface="p2p-dev-wlan0",
    )

    # Start hostp2pd in interactive mode
    with hostp2pd:
        print("hostp2pd is running, waiting for connections...")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    main()
