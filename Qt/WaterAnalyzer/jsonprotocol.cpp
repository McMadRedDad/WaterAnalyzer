#include "jsonprotocol.hpp"

const QString JsonProtocol::proto_version = "2.0.0";

JsonProtocol::JsonProtocol(QString server_version) {
  this->server_version = server_version;
  this->counter = 0;
}

QJsonObject JsonProtocol::construct_json(QString operation,
                                         QJsonObject parameters) {
  QJsonObject json{{"proto_version", JsonProtocol::proto_version},
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

QString JsonProtocol::get_server_version() { return server_version; }
