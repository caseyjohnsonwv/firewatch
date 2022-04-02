from utils.aws import DynamoDB


class ParkRecord:
    def __init__(self, park_id:int, park_name:str):
        self.park_id = park_id
        self.park_name = park_name

    def _to_dict(self):
        return {'park_id':self.park_id, 'park_name':self.park_name}
    
    def write_to_dynamo(self):
        DynamoDB.put_item(DynamoDB.PARKS_TABLE, self._to_dict())


class RideRecord:
    def __init__(self, ride_id:int, park_id:int, ride_name:str=None, park_name:str=None, wait_time:int=None, is_open:bool=None):
        self.ride_id = ride_id
        self.park_id = park_id
        self.ride_name = ride_name
        self.park_name = park_name
        self.wait_time = wait_time
        self.is_open = is_open

    def _to_dict(self):
        # return all non-null attributes
        out = {}
        for attr in vars(self):
            if self.__dict__[attr] is not None:
                out[attr] = self.__dict__[attr]
        return out
    
    def write_to_dynamo(self):
        DynamoDB.put_item(DynamoDB.RIDES_TABLE, self._to_dict())