from django.template.defaulttags import register

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get(list, key):
    return list[key]

@register.filter
def calculate_difference(target, previous_split):
    return len(target) - previous_split if isinstance(previous_split, int) else "NaN"

@register.filter
def calculate_percentage(target):
    return round(target * 100,3)