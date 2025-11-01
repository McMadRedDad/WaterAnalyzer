#ifndef JSONPROTOCOL_H
#define JSONPROTOCOL_H

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

class JsonProtocol {
public:
    JsonProtocol() {
        server_version = "";
        counter = -1;
    };
    JsonProtocol(QString server_version);

    QJsonObject ping();
    QJsonObject shutdown();
    QJsonObject import_gtiff(QString file, QString band);
    QJsonObject calc_preview(QString index, uint width, uint height);
    QJsonObject calc_index(QString index);
    QJsonObject set_satellite(QString satellite, QString proc_level);
    QJsonObject end_session();
    QJsonObject import_metafile(QString file);

    void    inc_counter();
    QString get_proto_version();
    QString get_server_version();
    quint32 get_counter();

private:
    QJsonObject construct_json(QString operation, QJsonObject parameters);

    static const QString proto_version;
    QString              server_version;
    qint32               counter;
};

#endif // JSONPROTOCOL_H
