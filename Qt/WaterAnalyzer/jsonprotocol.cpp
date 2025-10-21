#include "jsonprotocol.hpp"

const QString JsonProtocol::proto_version = "2.1.5";

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

QJsonObject JsonProtocol::import_gtiff(QString file) {
    return construct_json("import_gtiff", QJsonObject{{"file", file}});
}

QJsonObject JsonProtocol::calc_preview(int r, int g, int b, uint width, uint height) {
    return construct_json("calc_preview",
                          QJsonObject{{"ids", QJsonArray{(int) r, (int) g, (int) b}}, {"width", (int) width}, {"height", (int) height}});
}

QJsonObject JsonProtocol::calc_index(QString index, QList<int> ids) {
    QJsonArray ids_arr;
    for (uint id : ids) {
        ids_arr.append((int) id);
    }
    return construct_json("calc_index", QJsonObject{{"index", index}, {"ids", ids_arr}});
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
