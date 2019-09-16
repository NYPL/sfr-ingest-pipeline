from collections import defaultdict
from math import sqrt
import re
import string
import warnings

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import MinMaxScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import ConvergenceWarning

from helpers.logHelpers import createLog


class TextSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.key]


class NumberSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[[self.key]]


class KModel:
    LOGGER = createLog('kMeans')
    
    def __init__(self, instances):
        self.instances = instances
        self.df = None
        self.clusters = defaultdict(list)
    
    def createPipeline(self):
        return Pipeline([
            ('union', FeatureUnion(
                transformer_list=[
                    ('place', Pipeline([
                        ('selector', TextSelector(key='place')),
                        ('tfidf', TfidfVectorizer(
                            preprocessor=KModel.pubProcessor,
                            stop_words='english',
                            strip_accents='unicode',
                            analyzer='char_wb',
                            ngram_range=(2,4))
                        )
                    ])),
                    ('publisher', Pipeline([
                        ('selector', TextSelector(key='publisher')),
                        ('tfidf', TfidfVectorizer(
                            preprocessor=KModel.pubProcessor,
                            stop_words='english',
                            strip_accents='unicode',
                            analyzer='char_wb',
                            ngram_range=(2,4))
                        )
                    ])),
                    ('date', Pipeline([
                        ('selector', NumberSelector(key='pubDate')),
                        ('scaler', MinMaxScaler())
                    ]))
                ],
                transformer_weights={
                    'place': 1.0,
                    'publisher': 1.0,
                    'date': 1.5
                }
            )),
            ('kmeans', KMeans(
                n_clusters=self.currentK,
                n_jobs=4,
                n_init=20,
                init='random',
                max_iter=500
            ))
        ])
    
    @classmethod
    def pubProcessor(cls, raw):
        if isinstance(raw, list):
            raw = ', '.join(filter(None, raw))
        if raw is not None:
            raw = raw.replace('&', 'and')
            cleanStr = raw.translate(
                str.maketrans('', '', string.punctuation)
            ).lower()
            cleanStr = cleanStr\
                .replace('sn', '')\
                .replace('place of publication not identified', '')\
                .replace('publisher not identified', '')
            cleanStr = re.sub(r'\s+', ' ', cleanStr)
            cls.LOGGER.debug('Cleaned string {} to {} for processing'.format(
                raw, cleanStr
            ))
            return cleanStr
        cls.LOGGER.debug('Unable to clean NoneType, returning empty string')
        return ''

    def createDF(self):
        self.LOGGER.info('Generating DataFrame from instance data')
        self.df = pd.DataFrame([
            {
                'place': i.pub_place if i.pub_place else '',
                'publisher': KModel.getPublisher(i.agent_instances),
                'pubDate': KModel.getPubDateFloat(i.dates),
                'edition': i.edition_statement,
                'rowID': i.id
            }
            for i in self.instances
            if KModel.emptyInstance(i) != False
        ])
        self.maxK = len(self.df.index) if len(self.df.index) > 1 else 2
    
    @staticmethod
    def emptyInstance(instance):
        return bool(instance.pub_place or\
            KModel.getPubDateFloat(instance.dates) or\
            KModel.getPublisher(instance.agent_instances))

    @classmethod
    def getPubDateFloat(cls, dates):
        for d in dates:
            if d.date_type == 'pub_date' and d.date_range:
                cls.LOGGER.debug('Found publication date {}'.format(
                    d.display_date
                ))
                lowerYear = d.date_range.lower.year if d.date_range.lower else None
                upperYear = d.date_range.upper.year if d.date_range.upper else None
                if lowerYear and upperYear:
                    return (upperYear + lowerYear) / 2
                elif lowerYear:
                    return lowerYear
                elif upperYear:
                    return upperYear
        
        cls.LOGGER.debug('Unable to locate publication date')
        return 0
    
    @classmethod
    def getPublisher(cls, agent_rels):
        publishers = [
            a.agent.name for a in agent_rels
            if a.role == 'publisher'
        ]
        return '; '.join(sorted(list(set(publishers))))
    
    def generateClusters(self):
        self.LOGGER.info('Generating Clusters from instances')
        try:
            self.getK()
            self.LOGGER.debug('Setting K to {}'.format(self.k))
        except ZeroDivisionError:
            self.LOGGER.debug('Single instance found setting K to 1')
            self.k = 1
        
        try:
            labels = self.cluster(self.k)
        except ValueError as err:
            labels = [0] * len(self.instances)
        
        for n, item in enumerate(labels):
            self.clusters[item].append(self.df.loc[[n]])
    
    def getK(self):
        self.LOGGER.info('Calculating number of clusters, max {}'.format(
            self.maxK
        ))
        warnings.filterwarnings('error')
        wcss = []
        for i in range(1, self.maxK):
            try:
                wcss.append((self.cluster(i, score=True), i))
            except ConvergenceWarning:
                self.LOGGER.info('Exceeded number of distinct clusters, break')
                break
            except Exception:
                pass
        
        x1, y1 = wcss[0][1], wcss[0][0]
        x2, y2 = wcss[len(wcss) - 1][1], wcss[(len(wcss) - 1)][0]

        distances = []
        denominator = sqrt((y2 - y1)**2 + (x2 - x1)**2)
        for i in range(len(wcss)):
            x0 = i + 1
            y0 = wcss[i][0]

            numerator = abs((y2 - y1)*x0 - (x2 + x1)*y0 + x2*y1 - y2*x1)
            distances.append(numerator/denominator)
        
        self.k = distances.index(max(distances)) + 2
    
    def cluster(self, k, score=False):
        self.currentK = k
        self.LOGGER.debug('Generating cluster for k={}'.format(k))
        pipeline = self.createPipeline()
        if score is True:
            self.LOGGER.debug('Returning score for n_clusters estimation')
            pipeline.fit(self.df)
            return pipeline['kmeans'].inertia_
        else:
            self.LOGGER.debug('Returning model prediction')
            return pipeline.fit_predict(self.df)
    
    def parseEditions(self):
        eds = []
        self.LOGGER.info('Generating editions from clusters')
        for clust in dict(self.clusters):
            yearEds = defaultdict(list)
            self.LOGGER.info('Parsing cluster {}'.format(clust))
            for ed in self.clusters[clust]:
                self.LOGGER.debug('Adding instance to {} edition'.format(
                    ed.iloc[0]['pubDate']
                ))
                yearEds[ed.iloc[0]['pubDate']].append({
                    'pubDate': ed.iloc[0]['pubDate'],
                    'publisher': ed.iloc[0]['publisher'],
                    'pubPlace': ed.iloc[0]['place'],
                    'rowID': ed.iloc[0]['rowID'],
                    'edition': ed.iloc[0]['edition']
                })
            eds.extend([(year, data) for year, data in yearEds.items()])
            eds.sort(key=lambda x: x[0])

        return eds
            
