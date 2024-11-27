from rest_framework import serializers
from .models import Dish, Category, Table

# Serializer cho Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'image']

# Serializer cho Dish


class DishSerializer(serializers.ModelSerializer):
    category = CategorySerializer()  # Bao gồm thông tin danh mục trong món ăn

    class Meta:
        model = Dish
        fields = ['id', 'name', 'ingredients', 'price',
                  'discounted_price', 'is_available', 'category', 'image']

# Serializer cho Table (Bàn ăn)


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'name', 'is_occupied']
