#ifndef MAINWINDOW_HPP
#define MAINWINDOW_HPP

#include "importpage.hpp"
#include "jsonprotocol.hpp"
#include "processpage.hpp"
#include "resultpage.hpp"
#include <QMainWindow>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QTimer>

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

enum PAGE { BAD = -1, IMPORT, IMPORT_CUSTOM_BANDS, SELECTION, RESULT };

struct DATASET {
    QString filename = "";
    int     id = -1;
    QString url = "";
    uint    width = -1, height = -1;
    QString projection = "", unit = "";
    double  origin[2] = {0.0, 0.0};
    double  pixel_size[2] = {0.0, 0.0};
};

struct STATE {
    ImportPage            *import_p;
    ProcessPage           *process_p;
    ResultPage            *result_p;
    PAGE                   page;
    QDir                   dir;
    uint                   curr_req_id;
    QMap<QString, DATASET> files; // band/index: DATASET
};

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_pb_back_clicked();
    void on_pb_show_log_clicked();

signals:
    void to_satellite_select_page();
    void metadata(QStringList);

private:
    STATE                  self;
    QHostAddress           backend_ip;
    quint16                backend_port;
    QNetworkAccessManager *net_man;
    JsonProtocol           proto;

    Ui::MainWindow *ui;
    QTimer          timer_status;

    void       send_request(QString type, QJsonObject data, QMap<QString, QString> options = {});
    void       handle_error(QNetworkReply *response);
    void       process_get(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options = {});
    void       process_post(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options = {});
    QList<int> select_bands_for_index(QString index);
    QString    get_type_by_index(QString index);
    QString    get_index_by_type(QString type);

    void set_status_message(bool good, QString message, short msec = 3000);
    void append_log(QString type, QString line);
    void change_page(PAGE to);
    void lock_interface(bool on);
    void closeEvent(QCloseEvent *e) override;
};
#endif // MAINWINDOW_HPP
