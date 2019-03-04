const bodybuilder = require('bodybuilder')

module.exports = (app, respond, handleError) => {
    app.post('/sfr/search', async (req, res) => {
    
        const params = req.body

        const searchRes = await simpleSearch(params, res)

        respond(res, searchRes, params)
    })

    app.get('/sfr/search', async (rec, res) => {

        const params = rec.query
        
        const searchRes = await simpleSearch(params, res)

        respond(res, searchRes, params)
    })

    const simpleSearch = (params, res) => {

        if(!('field' in params) || !('query' in params)){
            handleError(res, {
                "name": "InvalidParameterError",
                "message": "Your POST request must include either queries or filters"
            })
        }
    
        const { field, query } = params
        
        const pageNum = (params.page) ? params.page : 0
        const perPage = (params.per_page) ? params.per_page : 10
    
        const body = bodybuilder()
    
        body.size(perPage)
        body.from(pageNum)
    
        // Catch case where escape charaacter has been escaped and reduce to a single
        // escape character
        const queryTerm = query.replace(/[\\]+([^\w\s]{1})/g, '\$1')

        switch(field){
            case "author":
                body.query('bool', b => b
                        .query('bool', c => c
                        .orQuery("nested", {path: "agents", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                        .orQuery("nested", {path: "instances.agents", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                    )                
                )
                break
            case "subject":
                body.query("nested", {path: "subjects", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                break
            case "title":
                body.query('query_string', {"fields": ["title", "alt_titles"], "query": queryTerm, "default_operator": "and"})
                break
            case "keyword":
            default:
                body.query('bool', b => b
                    .query('bool', c => c
                        .orQuery("query_string", "query", queryTerm, {default_operator: "and"})
                        .orQuery("nested", {path: "subjects", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                        .orQuery("nested", {path: "agents", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                        .orQuery("nested", {path: "instances", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                        .orQuery("nested", {path: "instances.agents", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                        .orQuery("nested", {path: "instances.items", query: {query_string: {query: queryTerm, default_operator: "and"}}})
                    )
                )
                break
        }

        // Filter block, used to search/filter data on specific terms. This can serve
        // as the main search field (useful for browsing) but generally it narrows
        // results in conjunction with a query
        if ('filters' in params) {
            params["filters"].map((filter) => {
            switch(filter['field']){
                case "year":
                    body.query("nested", {path: "instances", query: {range: {"instances.pub_date": {gte: filter["value"], lte: filter["value"]}}}})
                    break
                case "language":
                    body.query("nested", {path: "language", query: {term: {"language.language": filter["value"]}}})
                    body.query("nested", {path: "instances.language", query: {term: {"instances.language.language": filter["value"]}}})
                    break
                default:
                    app.logger('Not configured to handle this filter, ignoring')
                    break
            }
            })
        }
    
        // Sort block, this orders the results. Can be asc/desc and on any field
        if ('sort' in params) {
            params["sort"].map((sort) => {
            switch(sort["field"]){
                default:
                body.sort(sort['field'], sort['dir'])
            }
            })
        }
    
        // Aggregations block, this should be more complicated to enable full features
        // but essentially this builds an object of record counts grouped by a term
        // For example it can group works by authors/agents. This is used to
        // display browse options and do other metrics related querying
        if ('aggregations' in params) {
            params["aggregations"].map((agg) => {
            body.aggregation(agg['type'], agg['field'])
            })
        }
        
        const esQuery = {
            index: process.env.ELASTICSEARCH_INDEX,
            body: body.build()
        }
        
        return new Promise((resolve) => {
            app.client.search(esQuery)
                .then((resp) => {
                    resolve(resp)
                })
                .catch((error) => handleError(res, error))
        })
    }
}