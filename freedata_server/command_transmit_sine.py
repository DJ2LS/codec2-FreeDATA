from command import TxCommand

class TransmitSine(TxCommand):
    def transmit(self, modem):
        modem.transmit_sine()
        # Code for debugging morse stuff...
        #modem.transmit_morse(0,0,[b''])