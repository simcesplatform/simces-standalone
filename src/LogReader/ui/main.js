/* Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
This source code is licensed under the MIT license. See LICENSE in the repository root directory.
Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi> */
function updateLatestQuery(query) {
    document.getElementById("latest_query").innerHTML  = query;
}

function getHostname() {
    return window.location.href.slice( 0, -1 );
}

function getSimulations() {
    const fromDate = document.getElementById("simulations_fromDate").value;
    const toDate = document.getElementById("simulations_toDate").value;
    let url = getHostname() + "/simulations";
    let queryParams = [];
    if ( fromDate !== "" ) {
        queryParams.push( "fromDate=" +fromDate );
    }
    
    if ( toDate !== "" ) {
        queryParams.push( "toDate=" +toDate );
    }
    
    if ( queryParams.length > 0 ) {
        url = url +"?" +queryParams.join("&");
    }
    
    updateLatestQuery(url);
    window.open(url);
}

function getSimulation() {
    const simulationId = document.getElementById("simulations_simulationId").value;
    const fullUrl = getHostname() + "/simulations/" + simulationId;
    updateLatestQuery(fullUrl);
    window.open(fullUrl);
}

function getSimulationMessages() {
    const simulationId = document.getElementById("messages_simulationId").value;
    const topic = document.getElementById("messages_topic").value;
    const process = document.getElementById("messages_process").value;
    const epoch = document.getElementById("messages_epoch").value;
    const startEpoch = document.getElementById("messages_startEpoch").value;
    const endEpoch = document.getElementById("messages_endEpoch").value;
    const fromSimDate = document.getElementById("messages_fromSimDate").value;
    const toSimDate = document.getElementById("messages_toSimDate").value;
    const onlyWarnings = document.getElementById("messages_onlyWarnings").checked;

    const url = getHostname() + "/simulations/" + simulationId + "/messages?";
    query_params = []
    if (topic !== "") query_params.push("topic=" + topic.replace(/#/g, "%23"));
    if (process !== "") query_params.push("process=" + process);
    if (epoch !== "") query_params.push("epoch=" + epoch);
    if (startEpoch !== "") query_params.push("startEpoch=" + startEpoch);
    if (endEpoch !== "") query_params.push("endEpoch=" + endEpoch);
    if (fromSimDate !== "") query_params.push("fromSimDate=" + fromSimDate);
    if (toSimDate !== "") query_params.push("toSimDate=" + toSimDate);
    if (onlyWarnings) query_params.push("onlyWarnings=true");
    const fullUrl = url + query_params.join("&");

    updateLatestQuery(fullUrl);
    window.open(fullUrl);
}

function getSimulationInvalidMessages() {
    const simulationId = document.getElementById("invalid_messages_simulationId").value;
    const topic = document.getElementById("invalid_messages_topic").value;
    const url = getHostname() + "/simulations/" + simulationId + "/messages/invalid?";
    query_params = []
    if (topic !== "") query_params.push("topic=" + topic.replace(/#/g, "%23"));
    const fullUrl = url + query_params.join("&");

    updateLatestQuery(fullUrl);
    window.open(fullUrl);
}

function getSimulationTimeseries() {
    const simulationId = document.getElementById("timeseries_simulationId").value;
    const attrs = document.getElementById("timeseries_attrs").value;
    const topic = document.getElementById("timeseries_topic").value;
    const process = document.getElementById("timeseries_process").value;
    const epoch = document.getElementById("timeseries_epoch").value;
    const startEpoch = document.getElementById("timeseries_startEpoch").value;
    const endEpoch = document.getElementById("timeseries_endEpoch").value;
    const fromSimDate = document.getElementById("timeseries_fromSimDate").value;
    const toSimDate = document.getElementById("timeseries_toSimDate").value;
    const format = document.querySelector("input[name=timeseries_format]:checked").value

    const url = getHostname() + "/simulations/" + simulationId + "/timeseries?";
    query_params = []
    if (attrs !== "") query_params.push("attrs=" + attrs);
    if (topic !== "") query_params.push("topic=" + topic.replace(/#/g, "%23"));
    if (process !== "") query_params.push("process=" + process);
    if (epoch !== "") query_params.push("epoch=" + epoch);
    if (startEpoch !== "") query_params.push("startEpoch=" + startEpoch);
    if (endEpoch !== "") query_params.push("endEpoch=" + endEpoch);
    if (fromSimDate !== "") query_params.push("fromSimDate=" + fromSimDate);
    if (toSimDate !== "") query_params.push("toSimDate=" + toSimDate);
    if (format !== "") query_params.push("format=" + format);
    const fullUrl = url + query_params.join("&");

    updateLatestQuery(fullUrl);
    window.open(fullUrl);
}

window.addEventListener("load", function() {
    const mainTableWidth = document.getElementById("main_table").getBoundingClientRect().width + "px";
    document.getElementById("latest_query_table").style.width = mainTableWidth;
});