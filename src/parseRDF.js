import {parseString} from 'xml2js'

const storeFields = [
    ["dcterms:title", "title"],
    ["dcterms:alternative", "altTitle"],
    ["dcterms:publisher", "publisher"],
    ["dcterms:rights", "rightsStmt"],
    ["pgterms:marc010", "lccn"],
    ["dcterms:issued", "created"],
    ["pgterms:marc901", "coverImageUrl"]
]

const entityFields = [
    ["pgterms:birthdate", "birth"],
    ["pgterms:deathdate", "death"],
    ["pgterms:name", "name"]
]

const fileFields = [
    ["dcterms:modified", "updated"],
    ["dcterms:extent", "size"]
]

const subjAuthRegex = /\/([A-Z]+)$/

export const parseRDF = (data, lcRels, callback) => {
    let rdfData = data["data"]["repository"]["object"]
    let rdfText = rdfData["text"]
    parseString(rdfText, (err, result) => {
        let gutenbergData = loadGutenbergRecord(result["rdf:RDF"], lcRels)
        callback(gutenbergData)
    })
}

const loadGutenbergRecord = (rdf, lcRels) => {
    let bibRecord = {}
    let ebook = rdf["pgterms:ebook"][0]
    let work = rdf["cc:Work"][0]
    
    bibRecord["formats"] = getFormats(ebook["dcterms:hasFormat"])
    bibRecord["subjects"] = getSubjects(ebook["dcterms:subject"])
    bibRecord["entities"] = getEntities(ebook, lcRels)
    storeFields.map(field => {
        bibRecord[field[1]] = getRecordField(ebook, field[0])
    })
    bibRecord["license"] = getFieldAttrib(work["cc:license"][0], "rdf:resource")
    let languageCont = ebook["dcterms:language"][0]["rdf:Description"][0]
    bibRecord["language"] = getRecordField(languageCont, "rdf:value")
    return bibRecord
}

const getEntities = (ebook, lcRels) => {
    let entities = []
    try{
        let creator = getEntity(ebook["dcterms:creator"][0]["pgterms:agent"][0], "author")
        entities.push(creator)
    } catch(e) {
        if (e instanceof TypeError){
            console.log("No creator associated")
        } else {
            throw e
        }
    }
    lcRels.map((rel) => {
        let roleTerm = 'marcrel:' + rel[0]
        if(roleTerm in ebook){
            let ent = getEntity(ebook[roleTerm][0]["pgterms:agent"][0], rel[1])
            entities.push(ent)
        }
    })
    return entities
}

const getEntity = (entity, role) => {
    let entRec = {
        "role": role
    }
    entityFields.map(field => {
        entRec[field[1]] = getRecordField(entity, field[0])
    })

    entRec["aliases"] = entity["pgterms:alias"]
    if( "pgterms:webpage" in entity){
        entRec["webpage"] = getFieldAttrib(entity["pgterms:webpage"][0], "rdf:resource")
    }
    return entRec
}

const getSubjects = (subjects) => {
    let terms = []
    if(!subjects) return terms
    subjects.map(subject => {
        let subjRecord = subject["rdf:Description"][0]
        let authURL = getFieldAttrib(subjRecord["dcam:memberOf"][0], "rdf:resource")

        let term = {
            "term": getRecordField(subjRecord, "rdf:value"),
            "authority": subjAuthRegex.exec(authURL)[1]
        }
        terms.push(term)
    })
    return terms
}

const getFormats = (formats) => {
    let epubs = []
    if(!formats) return epubs
    formats.map(format => {
        let fileFormat = format["pgterms:file"][0]
        let url = getFieldAttrib(fileFormat, "rdf:about")
        if (url.includes(".epub")){
            let epub = {
                "url": url
            }
            fileFields.map(field => {
                epub[field[1]] = getRecordField(fileFormat, field[0])
            })
            epubs.push(epub)
        }
    })
    return epubs
}

const getRecordField = (rec, field) => {
    try{
        if(typeof rec[field][0] === 'object'){
            return rec[field][0]._
        } else {
            return rec[field][0]
        }

    } catch (e) {
        if (e instanceof TypeError){
            return ''
        } else {
            throw e
        }
    }
}

const getFieldAttrib = (field, attrib) => {
    let attribs = field["$"]
    return attribs[attrib]
}
