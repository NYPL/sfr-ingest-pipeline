import csvtojson from 'csvtojson'
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

const lcRels = loadLCRels()

export const parseRDF = (data) => {
    let rdfData = data["data"]["repository"]["object"]
    let rdfText = rdfData["text"]
    parseString(rdfText, (err, result) => {
        loadGutenbergRecord(result["rdf:RDF"])
    })
}

const loadGutenbergRecord = (rdf) => {
    let bibRecord = {}
    let ebook = rdf["pgterms:ebook"][0]
    let work = rdf["cc:Work"][0]

    // TODO
    // 1) Load license URL from work record
    // 2) Load Subjects into record
    // 3) Load creator and other entities into record
    // 3a) Handle multiple aliases
    // 4) Scan RDF records to be sure that we aren't missing any fields
    console.log(work)
    console.log(ebook["dcterms:subject"][0]["rdf:Description"][0])
    console.log(ebook["dcterms:creator"][0]["pgterms:agent"][0])

    bibRecord["formats"] = getFormats(ebook["dcterms:hasFormat"])
    storeFields.map(field => {
        bibRecord[field[1]] = getRecordField(ebook, field[0])
    })
    console.log(bibRecord)
}

const getFormats = (formats) => {
    let epubs = []
    formats.map(format => {
        let fileFormat = format["pgterms:file"][0]
        url = getFieldAttrib(format, "rdf:about")
        if (url.includes(".epub")){
            let epub = {
                "url": url
            }
            fileFields.map(field => {
                epub[field[1]] = getRecordField(format, field[0])
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

const loadLCRels = () => {
    let rels = {}
    csvtojson().fromFile("./lc_relators.csv").then((obj) => {
        obj.forReach((rel) => {
            rels[rel[1]] = rel[2].toLowerCase()
        })
        return rels
    })
}
