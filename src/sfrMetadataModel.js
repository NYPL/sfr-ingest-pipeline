export class InstanceRecord {
  constructor(title, language) {
    this.title = title
    this.subtitle = null
    this.altTitle = null
    this.pubPlace = null
    this.pubDate = null
    this.language = language
    this.edition = null
    this.editionStatement = null
    this.tableOfContents = null
    this.copyrightDate = null
    this.agents = []
    this.identifiers = []
    this.formats = []
    this.measurements = []
  }

  addAgent(name, roles, aliases, birth, death, link){
    this.agents.push(new Agent(name, roles, aliases, birth, death, link))
  }
}

export class Agent {
  constructor(name, role, aliases, birth, death, link) {
    this.name = name
    this.sortName = null
    this.roles = role
    this.lcnaf = null
    this.viaf = null
    this.biography = null
    this.aliases = aliases
    this.birthDate = birth
    this.deathDate = death
    this.link = link
  }
}



export class Identifier {
  constructor(type, identifier, weight) {
    this.type = type
    this.identifier = identifier
    this.weight = weight
  }
}


export class Format {
  constructor(contentType, link, modified) {
    this.contentType = contentType
    this.drm = null
    this.measurements = []
    this.modified = modified

    if (link instanceof Link || link == null) this.link = link
    else this.link = this.setLink(link)

    this.rightsURI = null
  }

  setLink(linkObj){
    let formatLink = new Link(
      linkObj.url,
      linkObj.mediaType,
      linkObj.relType
    )
    if(linkObj.content) formatLink.content = linkObj.content

    if(linkObj.thumbnail) formatLink.thumbnail = linkObj.thumbnail

    return formatLink
  }

  addMeasurement(quantity, value, weight, takenAt){
    this.measurements.push(new Measurement(quantity, value, weight, takenAt))
  }
}


export class Link {
  constructor(url, mediaType, relType){
    this.url = url
    this.mediaType = mediaType
    this.content = null
    this.relType = relType
    this.thumbnail = null
  }
}


export class Subject {
  constructor(subjectType, value, weight){
    this.type = subjectType
    this.identifier = null
    this.value = value
    this.weight = weight
    this.measurements = []
  }
}


export class Measurement {
  constructor(quantity, value, weight, takenAt){
    this.quantity = quantity
    this.value = value
    this.weight = weight
    this.takenAt = null
  }
}

export class WorkRecord {
  constructor(source) {
    this.source = source
    this.identifiers = []
    this.instances = []
    this.subjects = []
    this.agents = []
    this.links = []
    this.measurements = []
    this.license = null
    this.language = null
    this.title = null
    this.subTitle = null
    this.altTitle = null
    this.rightsStatement = null
    this.issued = null
    this.published = null
    this.medium = null
    this.series = null
    this.seriesPosition = null
    this.primaryIdentifier = null
  }

  addIdentifier(type, identifier, weight){
    this.identifiers.push(new Identifier(type, identifier, weight))
  }

  addInstance(title, language){
    this.instances.push(new InstanceRecord(title, language))
  }

  addSubject(subjectType, identifier, value, weight){
    this.subjects.push(new Subject(subjectType, identifier, value, weight))
  }

  addAgent(name, roles, aliases, birth, death, link){
    this.agents.push(new Agent(name, roles, aliases, birth, death, link))
  }

  addMeasurement(quantity, value, weight, takenAt){
    this.measurements.push(new Measurement(quantity, value, weight, takenAt))
  }
}
