import os
import json
from rest_framework import views
from rest_framework.response import Response


class ScrewDataView(views.APIView):
    def get(self, request):
        with open('control/screw.json', 'r',encoding="utf-8") as f:
            data = json.load(f)
        with open('control/weight.json', 'r',encoding="utf-8") as f2:
            data2 = json.load(f2)

        speed = data['speed']
        current = data['current']
        direction = data['direction']
        weight = data2['weight']
        return Response({'speed': speed, 'current': current, 'direction': direction,
                         'weight': weight})

class ScrewConfigView(views.APIView):
    def get(self, request):
        with open('control/screw_config.json', 'r',encoding="utf-8") as f:
            data = json.load(f)
        return Response(data,status=200)

    def post(self, request):
        data = request.data
        print('xxxx {}'.format(data))
        # speed = data['speed']
        # power = data['power']
        # direction = data['direction']
        with open('control/screw_config.json', 'r',encoding="utf-8") as f:
            old_data = json.load(f)
        old_data.update(data)
        with open('control/screw_config.json', 'w',encoding="utf-8") as f:
            json.dump(old_data, f)
        return Response({'msg':'change ok'},status=200)

class HelloView(views.APIView):
    def get(self, request):
        return Response({'hello':'world'},status=200)


class AdjustScrewConfigView(views.APIView):
    def get(self, request):
        with open('control/adjust_screw_config.json', 'r',encoding="utf-8") as f:
            data = json.load(f)
        return Response(data,status=200)

    def post(self, request):
        data = request.data
        print('xxxx {}'.format(data))
        # speed = data['speed']
        # power = data['power']
        # direction = data['direction']
        with open('control/adjust_screw_config.json', 'r',encoding="utf-8") as f:
            old_data = json.load(f)
        old_data.update(data)
        with open('control/adjust_screw_config.json', 'w',encoding="utf-8") as f:
            json.dump(old_data, f)
        return Response({'msg':'change ok'},status=200)
