#ifndef CURVE_H
#define CURVE_H

#include "plotitem.h"
#include "point.h"

#include <QtGui/QPen>
#include <QtGui/QBrush>

#include <QtCore/QtConcurrentMap>

struct DataPoint
{
  qreal x;
  qreal y;
};

struct ScaleUpdater
{
    ScaleUpdater(qreal scale) {m_scale = scale;}
    void operator()(QGraphicsItem* item) {item->setScale(m_scale);}
    
private:
    qreal m_scale;
};

struct PointUpdater
{
    PointUpdater(int symbol, QColor color, int size, Point::DisplayMode mode, qreal scale)
    {
        m_symbol = symbol;
        m_color = color;
        m_size = size;
        m_mode = mode;
        m_scale = scale;
    }
    
    void operator()(Point* point)
    {
        point->set_symbol(m_symbol);
        point->set_color(m_color);
        point->set_size(m_size);
        point->set_display_mode(m_mode);
        point->setScale(m_scale);
    }
    
    private:
     int m_symbol;
     QColor m_color;
     int m_size;
     Point::DisplayMode m_mode;
     qreal m_scale;
};

struct Updater
{
    Updater(qreal scale, const QPen& pen, const QBrush& brush, const QPainterPath& path)
    {
        m_scale = scale;
        m_pen = pen;
        m_brush = brush;
        m_path = path;
    }
    
    void operator()(QGraphicsPathItem* item)
    {
        item->setBrush(m_brush);
        item->setPen(m_pen);
        item->setScale(m_scale);
        item->setPath(m_path);
    }
    
    qreal m_scale;
    QPen m_pen;
    QBrush m_brush;
    QPainterPath m_path;
};
  
typedef QList< DataPoint > Data;

class Curve : public PlotItem
{
  
public:
  enum Style {
    NoCurve = Qt::NoPen,
    Lines = Qt::SolidLine,
    Sticks,
    Steps,
    Dots = Qt::DotLine,
    UserCurve = 100
  };
  
  /**
   * @brief Default constructor
   * 
   * Constructs a Curve from a series of data points
   *
   * @param xData A list of x coordinates of data points
   * @param yData A list of y coordinates of data points
   * @param parent parent item
   * @param scene if this is not 0, the Curve is automatically added to it
   **/
  Curve(const QList< double >& xData, const QList< double >& yData, QGraphicsItem* parent = 0, QGraphicsScene* scene = 0);
  Curve(QGraphicsItem* parent = 0, QGraphicsScene* scene = 0);
  /**
   * Default destructor
   *
   **/
  virtual ~Curve();
    
  /**
   * @brief Update the curve
   * 
   * Moves all the points to their current locations, and changes their color, shape and size. 
   * 
   * @note this method is optimized for cases where only one or two of the curve's properties have been changed. 
   * If there were multiple changes since the last update, updateAll() is probably faster. 
   *
   **/
   virtual void updateProperties();
  
  /**
   * @brief Updates all curve's properties
   * This methods updates all the curve's properties at once, without checking what needs updating. 
   * It is therefore faster for updates that change more than one property at once
   * 
   * @sa update()
   * 
   **/
  virtual void updateAll();
  
  /**
   * @brief ...
   *
   * @param x ...
   * @param y ...
   * @param size ...
   * @param parent ... Defaults to 0.
   * @return QGraphicsItem*
   **/
  Point* pointItem(qreal x, qreal y, int size = 0, QGraphicsItem* parent = 0);
  
  QColor color() const;
  void setColor(const QColor& color);
  
  QPen pen() const;
  void setPen(QPen pen);
  
  QBrush brush() const;
  void setBrush(QBrush brush);
  
  int pointSize() const;
  void setPointSize(int size);
  
  int symbol() const;
  void setSymbol(int symbol);
  
  bool isContinuous() const;
  void setContinuous(bool continuous);

  Data data() const;
  void setData(const QList<qreal> xData, const QList<qreal> yData);
  
  virtual QTransform graphTransform() const;
  virtual void setGraphTransform(const QTransform& transform);
  
  QRectF graphArea() const;
  void setGraphArea(const QRectF& area);
  
  int style() const;
  void setStyle(int style);
  
  bool autoUpdate() const;
  void setAutoUpdate(bool autoUpdate);
  
  double zoom_factor();
  void set_zoom_factor(double factor);
  
  qreal max_x_value() const;
  qreal min_x_value() const;
  qreal max_y_value() const;
  qreal min_y_value() const;
    
  enum UpdateFlag
  {
    UpdateNumberOfItems = 0x01,
    UpdatePosition = 0x02,
    UpdateSymbol = 0x04,
    UpdateSize = 0x08,
    UpdatePen = 0x10,
    UpdateBrush = 0x20,
    UpdateContinuous = 0x40,
    UpdateZoom = 0x80,
    UpdateAll = 0xFF
  };
  
  Q_DECLARE_FLAGS(UpdateFlags, UpdateFlag)
  
  void setDirty(UpdateFlags flags = UpdateAll);
  
  template <class Sequence, class Updater>
  void updateItems(Sequence& sequence, Updater updater, Curve::UpdateFlag flag);
  
private:    

  struct Bounds
  {
      qreal min;
      qreal max;
  };
    
  void checkForUpdate();
  void updateNumberOfItems();
  void changeContinuous();
  void updateBounds();
  
  QColor m_color;
  int m_pointSize;
  int m_symbol;
  int m_style;
  bool m_continuous;
  Data m_data;
  QTransform m_graphTransform;
  QPainterPath m_path;
  QList<Point*> m_pointItems;
  UpdateFlags m_needsUpdate;
  bool m_autoUpdate;
  QRectF m_graphArea;
    QGraphicsPathItem* m_lineItem;
    QPainterPath m_line;
    
    Bounds m_xBounds;
    Bounds m_yBounds;
  QPen m_pen;
  QBrush m_brush;
  double m_zoom_factor;
  QMap<UpdateFlag, QFuture<void> > m_currentUpdate;
};

template <class Sequence, class Updater>
void Curve::updateItems(Sequence& sequence, Updater updater, Curve::UpdateFlag flag)
{
    if (m_currentUpdate.contains(flag) && m_currentUpdate[flag].isRunning())
    {
        m_currentUpdate[flag].cancel();
    }
    m_currentUpdate[flag] = QtConcurrent::map(sequence, updater);
}


#endif // CURVE_H
