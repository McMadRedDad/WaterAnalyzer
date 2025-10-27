#include "jsonprotocol.hpp"

const QString JsonProtocol::proto_version = "3.0.1";

JsonProtocol::JsonProtocol(QString server_version) {
    this->server_version = server_version;
    this->counter = 0;
}

QJsonObject JsonProtocol::ping() {
    return construct_json("PING", QJsonObject());
}

QJsonObject JsonProtocol::shutdown() {
    return construct_json("SHUTDOWN", QJsonObject());
}

QJsonObject JsonProtocol::import_gtiff(QString file, ushort band) {
    return construct_json("import_gtiff", QJsonObject{{"file", file}, {"band", band}});
}

QJsonObject JsonProtocol::calc_preview(QString index, uint width, uint height) {
    return construct_json("calc_preview", QJsonObject{{"index", index}, {"width", (int) width}, {"height", (int) height}});
}

QJsonObject JsonProtocol::calc_index(QString index) {
    return construct_json("calc_index", QJsonObject{{"index", index}});
}

QJsonObject JsonProtocol::set_satellite(QString satellite, QString proc_level) {
    return construct_json("set_satellite", QJsonObject{{"satellite", satellite}, {"proc_level", proc_level}});
}

QJsonObject JsonProtocol::end_session() {
    return construct_json("end_session", QJsonObject());
}

void JsonProtocol::inc_counter() {
    counter++;
}

QJsonObject JsonProtocol::construct_json(QString operation, QJsonObject parameters) {
    QJsonObject json = {{"proto_version", JsonProtocol::proto_version},
                        {"server_version", this->server_version},
                        {"id", this->counter},
                        {"operation", operation},
                        {"parameters", parameters}};
    counter++;
    return json;
}

QString JsonProtocol::get_proto_version() {
    return JsonProtocol::proto_version;
}

QString JsonProtocol::get_server_version() {
    return server_version;
}

quint32 JsonProtocol::get_counter() {
    return counter;
}
