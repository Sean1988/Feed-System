import datetime
from haystack import indexes
from company.models import Tag, Company


class TagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tagType = indexes.CharField(model_attr='tagType')
    tagName = indexes.CharField(model_attr='tagName')
    content_auto = indexes.EdgeNgramField(model_attr='tagName')

    def get_model(self):
        return Tag

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()


class CompanyIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    rank = indexes.IntegerField(model_attr='rank')
    content_auto = indexes.EdgeNgramField(model_attr='name')
    
    def get_model(self):
        return Company

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

