export class InstanceRecord {
  constructor(title, language) {
    this.title = title
    this.sub_title = null
    this.pub_place = null
    this.pub_date = null
    this.language = language
    this.edition = null
    this.edition_statement = null
    this.table_of_contents = null
    this.copyright_date = null
    this.agents = []
    this.identifiers = []
    this.formats = []
    this.measurements = []
  }

  addAgent(name, roles, aliases, birth, death, link){
    this.agents.push(new Agent(name, roles, aliases, birth, death, link))
  }

  addIdentifier(type, identifier, weight){
    this.identifiers.push(new Identifier(type, identifier, weight))
  }
}

export class Agent {
  constructor(name, role, aliases, birth, death, link) {
    this.name = name
    this.sort_name = null
    this.roles = role
    this.lcnaf = null
    this.viaf = null
    this.biography = null
    this.aliases = aliases
    this.birth_date = birth
    this.death_date = death
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
    this.source = null
    this.content_type = contentType
    this.drm = null
    this.measurements = []
    this.modified = modified
    this.rights_uri = null
    this.identifiers = []

    if (link instanceof Link || link == null) this.link = link
    else this.link = this.setLink(link)

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

  addIdentifier(type, identifier, weight){
    this.identifiers.push(new Identifier(type, identifier, weight))
  }
}


export class Link {
  constructor(url, mediaType, relType){
    this.url = url
    this.media_type = mediaType
    this.content = null
    this.rel_type = relType
    this.rights_uri = null
    this.thumbnail = null
  }
}


export class Subject {
  constructor(subjectType, value, weight){
    this.authority = subjectType
    this.uri = null
    this.subject = value
    this.weight = weight
  }
}


export class Measurement {
  constructor(quantity, value, weight, takenAt){
    this.quantity = quantity
    this.value = value
    this.weight = weight
    this.taken_at = null
  }
}

export class WorkRecord {
  constructor() {
    this.identifiers = []
    this.instances = []
    this.subjects = []
    this.agents = []
    this.links = []
    this.measurements = []
    this.license = null
    this.language = null
    this.title = null
    this.sub_title = null
    this.alt_titles = null
    this.sort_title = null
    this.rights_statement = null
    this.issued = null
    this.published = null
    this.medium = null
    this.series = null
    this.series_position = null
    this.primary_identifier = null
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
