from django.core.management.base import BaseCommand
from users.models import State, Degmo, Magaalo


class Command(BaseCommand):
    help = 'Add Somali states with districts and cities'

    def handle(self, *args, **options):
        # Clear existing data
        Magaalo.objects.all().delete()
        Degmo.objects.all().delete()
        State.objects.all().delete()
        
        # Somali Federal States with their Districts and Cities
        locations = [
            {
                'name': 'Banadir',
                'degmo': [
                    {
                        'name': 'Hodan',
                        'magaalo': ['Hodan', 'Howlwad', 'Isgasho']
                    },
                    {
                        'name': 'Dayniile',
                        'magaalo': ['Dayniile', 'Xabadweyne']
                    },
                    {
                        'name': 'Wadajir',
                        'magaalo': ['Wadajir', 'Mareexan']
                    },
                    {
                        'name': 'Bondhere',
                        'magaalo': ['Bondhere', 'Shaqalaha']
                    },
                    {
                        'name': 'Heliwa',
                        'magaalo': ['Heliwa', 'Cabdifataax']
                    },
                    {
                        'name': 'Weydweyne',
                        'magaalo': ['Weydweyne', 'Garas Balley']
                    },
                    {
                        'name': 'Shibis',
                        'magaalo': ['Shibis', 'Xamar Jajab']
                    },
                    {
                        'name': 'Yaqshid',
                        'magaalo': ['Yaqshid', 'Calooli']
                    },
                    {
                        'name': 'Garas Balley',
                        'magaalo': ['Garas Balley']
                    },
                    {
                        'name': 'Abdiaziz',
                        'magaalo': ['Abdiaziz']
                    },
                ]
            },
            {
                'name': 'Jubaland',
                'degmo': [
                    {
                        'name': 'Kismayo',
                        'magaalo': ['Kismayo', 'Jagal']
                    },
                    {
                        'name': 'Bu\'aale',
                        'magaalo': ['Bu\'aale', 'Saakow']
                    },
                    {
                        'name': 'Jilib',
                        'magaalo': ['Jilib', 'Salagle']
                    },
                ]
            },
            {
                'name': 'South West State',
                'degmo': [
                    {
                        'name': 'Baidoa',
                        'magaalo': ['Baidoa', 'Bardaale']
                    },
                    {
                        'name': 'Buurhakaba',
                        'magaalo': ['Buurhakaba']
                    },
                    {
                        'name': 'Qansah Dhere',
                        'magaalo': ['Qansah Dhere']
                    },
                ]
            },
            {
                'name': 'Hirshabelle',
                'degmo': [
                    {
                        'name': 'Jowhar',
                        'magaalo': ['Jowhar', 'Balcad']
                    },
                    {
                        'name': 'Mahaday',
                        'magaalo': ['Mahaday']
                    },
                    {
                        'name': 'Cadale',
                        'magaalo': ['Cadale']
                    },
                ]
            },
            {
                'name': 'Galmudug',
                'degmo': [
                    {
                        'name': 'Galkayo',
                        'magaalo': ['Galkayo North', 'Galkayo South']
                    },
                    {
                        'name': 'Dhuusamarreeb',
                        'magaalo': ['Dhuusamarreeb']
                    },
                    {
                        'name': 'Gudud Wex',
                        'magaalo': ['Gudud Wex']
                    },
                ]
            },
            {
                'name': 'Puntland',
                'degmo': [
                    {
                        'name': 'Garowe',
                        'magaalo': ['Garowe', 'Bosaaso']
                    },
                    {
                        'name': 'Bosaaso',
                        'magaalo': ['Bosaaso', 'Carmo']
                    },
                    {
                        'name': 'Qandala',
                        'magaalo': ['Qandala']
                    },
                ]
            },
            {
                'name': 'Somaliland',
                'degmo': [
                    {
                        'name': 'Hargeisa',
                        'magaalo': ['Hargeisa', 'Berbera']
                    },
                    {
                        'name': 'Burco',
                        'magaalo': ['Burco', 'Taleex']
                    },
                    {
                        'name': 'Laascaanood',
                        'magaalo': ['Laascaanood', 'Xuddur']
                    },
                ]
            },
        ]
        
        for state_data in locations:
            state, created = State.objects.get_or_create(name=state_data['name'])
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created state: {state.name}'))
            
            for degmo_data in state_data['degmo']:
                degmo, created = Degmo.objects.get_or_create(
                    state=state,
                    name=degmo_data['name']
                )
                if created:
                    self.stdout.write(f'  Created district: {degmo.name}, {state.name}')
                
                for magaalo_name in degmo_data['magaalo']:
                    magaalo, created = Magaalo.objects.get_or_create(
                        degmo=degmo,
                        name=magaalo_name
                    )
                    if created:
                        self.stdout.write(f'    Created city: {magaalo.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully added Somali locations!'))
