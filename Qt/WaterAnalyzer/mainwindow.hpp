#ifndef MAINWINDOW_HPP
#define MAINWINDOW_HPP

#include "importpage.hpp"
#include "jsonprotocol.hpp"
#include "processpage.hpp"
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

struct STATE {
  ImportPage *import_p;
  ProcessPage *process_p;
  PAGE page;
  QDir dir;
  QMap<QString, QPair<QString, uint>> files; // band/index: {filename, id}
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

private:
  STATE self;
  QHostAddress backend_ip;
  quint16 backend_port;
  QNetworkAccessManager *net_man;
  JsonProtocol proto;

  Ui::MainWindow *ui;
  QTimer timer_status;

  void send_request(QString type, QJsonObject data);
  void handle_response(QNetworkReply *response);
  void process_get(QUrl endpoint, QByteArray body);
  void process_post(QUrl endpoint, QByteArray body);

  void set_status_message(bool good, QString message, short msec = 3000);
  void append_log(QString type, QString line);
  void change_page(PAGE to);

  void closeEvent(QCloseEvent *e) override;
};
#endif // MAINWINDOW_HPP
