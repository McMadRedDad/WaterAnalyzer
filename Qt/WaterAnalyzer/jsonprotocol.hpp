#ifndef JSONPROTOCOL_H
#define JSONPROTOCOL_H

#include <QJsonDocument>
#include <QJsonObject>

class JsonProtocol {
public:
  JsonProtocol() {
    server_version = "";
    counter = -1;
  };
  JsonProtocol(QString server_version);

  QJsonObject construct_json(QString operation, QJsonObject parameters);
  QString get_proto_version();
  QString get_server_version();

private:
  static const QString proto_version;
  QString server_version;
  qint32 counter;
};

#endif // JSONPROTOCOL_H
