from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank,SearchVectorField

from django.db.models import F
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.restaurants.models import MenuItem,Restaurants
from apps.restaurants.serializers import RestaurantListSerializer
from .serializers import MenuItemSearchSerializer
from core.pagination import StandardResultsPagination



class SearchPaginationResult(StandardResultsPagination):
    page_size=15
    max_page_size=30
    def get_paginated_response(self, data):
        return super().get_paginated_response(data)





class RestaurantSearchView(APIView):
    '''
    GET /search/restaurants/?q=pizza&city=kanpur&cuisine_type=PIZZA&ordering=-average_rating|average

    Working 
    1 - q -> utellize psql full text search(Postgres FTS) 
    2 - Filters -> applied on top of that (city, cuisine_type,is_premium,is_open)
    3- ordering -> ordering of search results (average rating , average preparation time )
      
        '''
    permission_classes =[AllowAny]
    def get(self,request):
        query = request.query_params.get('q','').strip()
        cuisine = request.query_params.get('cuisine_type','').strip()
        is_premium = request.query_params.get('is_premium','').strip()
        city = request.query_params.get('city','').strip()
        is_open=request.query_params.get('is_open','').strip()
        ordering= request.query_params.get('ordering','').strip()

        # base query
        queryset = Restaurants.objects.filter(is_active=True)

        #FTS
        if query:
            search_query=SearchQuery(query)
            
            search_vector = SearchVector('name',weight='A')+SearchVector('cuisine_type',weight='B')+SearchVector('description',weight='C')

            queryset = queryset.annotate(
                rank=SearchRank(search_vector,search_query)
            ).filter(rank__gte=0.1).order_by('-rank')

        #Filters 
        if cuisine:
            cuisines = request.query_params.getlist('cuisine_type')
            queryset=queryset.filter(cuisine_type__in=cuisines)
        
        if city:
            queryset=queryset.filter(city__iexact=city)
        
        if is_premium:
            queryset = queryset.filter(is_premium=is_premium.lower()=='true')
        
        if is_open:
            queryset=queryset.filter(is_open=is_open.lower()=='true')
        
        #default filter is no search query 
        if not query:
            allowed_ordering =[
                'average_rating','-average_rating',
                'delivery_fee','-delivery_fee',
                'avg_preparing_time','-avg_preparing_time'
            ]
            if ordering in allowed_ordering:
                queryset=queryset.order_by(ordering)
            else:
                queryset=queryset.order_by('-average_rating')
            
        #paginate 
        paginator = SearchPaginationResult()
        page = paginator.paginate_queryset(queryset,request)
        serializer = RestaurantListSerializer(page,many=True)
        return paginator.get_paginated_response(serializer.data)
            


class MenuItemSearchView(APIView):
    '''
    GET /search/menu-item/?q=pizza&is_veg=true,&max_price=300&min_price=100&sort_by=price
    
    Search across all restaurants - 
    Returns items with their restaurant info (helpful for client app to show the restaurant aside)
    
    '''
    permission_classes  = [AllowAny]

    def get(self,request):
        query = request.query_params.get('q','').strip()
        is_veg= request.query_params.get('is_veg','').strip()
        min_price=request.query_params.get('min_price','').strip()
        max_price=request.query_params.get('max_price','').strip()
        sort_by = request.query_params.get('sort_by','').strip()
        #only items from active , open restaurants 
        queryset  = MenuItem.objects.filter(
            is_available=True,
            category__restaurant__is_active=True,
            category__restaurant__is_open=True,
        ).select_related('category__restaurant').order_by('category__restaurant__average_rating')


        #Postgres FTS
        if query:
            search_query= SearchQuery(query)
            search_vector=(
                SearchVector('name' , weight='A') + SearchVector('description',weight='B')
            )
            queryset  = queryset.annotate(
                rank  = SearchRank(search_vector,search_query)
            ).filter(rank__gte=0.1).order_by('-rank')

        
        #filters 
        if is_veg:
            queryset = queryset.filter(is_veg=is_veg.lower()=='true')
        
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)

        if max_price:
            queryset = queryset.filter(base_price__lte = max_price)
        
        #Ordering 
        if sort_by:
            queryset = queryset.order_by(sort_by.lower())

        #pagination
        paginator = SearchPaginationResult()
        page = paginator.paginate_queryset(queryset,request)
        serializer = MenuItemSearchSerializer(page,many=True)
        return paginator.get_paginated_response(serializer.data)


#Auto Complete
class AutoCompleteSearch(APIView):
    '''
    GET search/auto/?q=piz

    Returns a quick suggestion as user types(use along with debounced search)
    if basically works as prefix matches as we're not going with elastic search 
    so we use icontains here 
    Only 10 results will be shown
    
    '''
    permission_classes = [AllowAny]

    def get(self,request):
        query  = request.query_params.get('q','').strip()

        if len(query)<2:
            # no search result here
            return Response({'restaurants':[],'items':[]})
        
        restaurants = Restaurants.objects.filter(
            name__icontains=query,
            is_active=True
        ).values('id','name','cuisine_type','city')[:10]

        menu_items = MenuItem.objects.filter(
            name__icontains=query,
            is_available=True,
            category__restaurant__is_active=True
        ).values('id','name','base_price',restaurant_name=F('category__restaurant__name'))[:10]


        return Response({
            'restaurants':list(restaurants),
            'items':list(menu_items)
        })
