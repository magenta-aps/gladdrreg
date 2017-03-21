from __future__ import unicode_literals

from django.db import models

class Base(models.Model):
  '''
  Abstract base class specifying a unique object.
  '''
  class Meta(object):
    abstract = True

  # aka sumiffiik
  objectID = models.UUIDField(primary_key=True)

class Locality(Base):
  # aka lokalitetskode
  code = models.IntegerField()
  # aka lokalitetsnavn
  name = models.CharField(max_length=255)
  # aka lokalitetstype
  type = models.CharField(max_length=255)

class Municipality(Base):
  # aka kommunekode
  code = models.PositiveSmallIntegerField()
  # aka kommunenavn
  name = models.CharField(max_length=255)

class PostalCode(Base):
  # aka postnummer
  code = models.PositiveSmallIntegerField()
  # aka by
  name = models.CharField(max_length=255)

class Road(Base):
  # aka vejkode
  code = models.PositiveIntegerField()
  # aka vejnavn
  name = models.CharField(max_length=255)

  # aka forkortetnavn_20_tegn
  shortname = models.CharField(max_length=20)

  # aka dansk_navn
  dkName = models.CharField(max_length=255)
  # aka groenlandsk_navn
  glName = models.CharField(max_length=255)
  # aka cpr_navn
  cprName = models.CharField(max_length=255)

class BNumber(Base):
  # aka nummer
  number = models.CharField(max_length=255)
  # aka kaldenavn
  name = models.CharField(max_length=255)
  # aka blokbetegnelse
  block = models.CharField(max_length=255)

  municipality = models.ForeignKey(Municipality)

class Address(Base):
  # aka husnummer
  houseNumber = models.CharField(max_length=255)
  # aka etage
  floor = models.CharField(max_length=255)

  locality = models.ForeignKey(Locality)
  bNumber = models.ForeignKey(BNumber)
  road = models.ForeignKey(Road)
  postalCode = models.ForeignKey(PostalCode)
