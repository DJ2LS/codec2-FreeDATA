from command import TxCommand
import base64

class FecCommand(TxCommand):

    def set_params_from_api(self, apiParams):
        self.mode = apiParams['mode']
        self.wakeup = apiParams['wakeup']
        payload_b64 = apiParams['payload']
    
        if len(payload_b64) % 4:
            raise TypeError
        self.payload = base64.b64decode(payload_b64)

        return super().set_params_from_api(apiParams)

    def build_wakeup_frame(self):
        return self.frame_factory.build_fec_wakeup(self.mode)

    def build_frame(self):
        return self.frame_factory.build_fec(self. mode, self.payload)
    
    def transmit(self, tx_frame_queue):
        if self.wakeup:
            tx_queue_item = self.make_modem_queue_item(self.get_c2_mode(), 1, 0, self.build_wakeup_frame())
            tx_frame_queue.put(tx_queue_item)

        tx_queue_item = self.make_modem_queue_item(self.get_c2_mode(), 1, 0, self.build_frame())
        tx_frame_queue.put(tx_queue_item)
